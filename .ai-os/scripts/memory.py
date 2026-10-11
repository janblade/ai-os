"""Evidence-backed, selective promotion of task notes with recoverable writes."""

import base64
import re
import subprocess
import uuid
from datetime import datetime, timezone

from context import context_item
from storage import RUNTIME, atomic_write, canonical_json, digest, git_value, memory_lock, read_json, workspace_path


ENTRY = re.compile(r"<!-- AIOS-ENTRY: ([a-f0-9]{32}) -->\n(.*?)\n<!-- /AIOS-ENTRY -->", re.DOTALL)
UNRESOLVED = re.compile(r"(?im)^\s*(?:[-*]\s*)?(?:\[ \]|TODO\b|FIXME\b|BUG\b|WIP\b)")
JOURNAL = RUNTIME + "/transaction.json"


def memory_path(root, name, directory):
    path = workspace_path(root, name)
    relative = path.relative_to(root).as_posix()
    if not relative.startswith(".ai-os/memory/" + directory + "/") or path.suffix != ".md":
        raise ValueError("Expected a Markdown file in memory/" + directory)
    return path


def state(path):
    return path.read_bytes() if path.exists() else None


def source_state(root, files):
    if not files:
        raise ValueError("Evidence needs explicit dependency files")
    return {item["source"]: item["sha256"] for item in
            (context_item(root, name, "verification dependency") for name in sorted(set(files)))}


def verify(root, files, command):
    if not command:
        raise ValueError("Verification needs a command after --")
    before = source_state(root, files)
    head = git_value(root, "rev-parse", "HEAD")
    result = subprocess.run(command, cwd=root, capture_output=True, check=False)
    unchanged = before == source_state(root, files) and head == git_value(root, "rev-parse", "HEAD")
    record = {"format": "AIOS-evidence/1", "created_at": datetime.now(timezone.utc).isoformat(),
              "head": head, "sources": before, "command_sha256": digest(canonical_json(command)),
              "stdout_sha256": digest(result.stdout), "stderr_sha256": digest(result.stderr),
              "returncode": result.returncode, "passed": result.returncode == 0 and unchanged}
    raw = canonical_json(record)
    path = workspace_path(root, RUNTIME + "/evidence/" + digest(raw) + ".json")
    atomic_write(path, raw)
    return {"evidence": path.relative_to(root).as_posix(), "passed": record["passed"],
            "returncode": result.returncode}


def validate_evidence(root, name):
    path = workspace_path(root, name)
    if not path.relative_to(root).as_posix().startswith(RUNTIME + "/evidence/"):
        raise ValueError("Expected local verification evidence")
    raw = path.read_bytes()
    record = read_json(path)
    if path.name != digest(raw) + ".json" or record.get("format") != "AIOS-evidence/1":
        raise ValueError("Evidence integrity check failed")
    if record.get("passed") is not True or record["returncode"] != 0:
        raise ValueError("Verification did not pass")
    if record["head"] != git_value(root, "rev-parse", "HEAD"):
        raise ValueError("Evidence is stale after a commit")
    if record["sources"] != source_state(root, record["sources"]):
        raise ValueError("Evidence dependency files changed; verify again")


def add_entry(root, task, note):
    path = memory_path(root, task, "tasks")
    text = context_item(root, note, "reviewed task note")["content"].strip()
    if not text or "AIOS-ENTRY" in text:
        raise ValueError("Note must be nonempty and contain no entry markers")
    identity = uuid.uuid4().hex
    with memory_lock(root):
        if workspace_path(root, JOURNAL).exists():
            raise ValueError("Recover the unfinished transaction first")
        before = path.read_bytes()
        after = before + ("\n<!-- AIOS-ENTRY: " + identity + " -->\n" + text
                          + "\n<!-- /AIOS-ENTRY -->\n").encode("utf-8")
        atomic_write(path, after)
    return {"entry_id": identity, "task_sha256": digest(after)}


def encoded(raw):
    return base64.b64encode(raw).decode("ascii") if raw is not None else None


def decoded(raw):
    return base64.b64decode(raw, validate=True) if raw is not None else None


def recover_locked(root):
    journal = workspace_path(root, JOURNAL)
    if not journal.exists():
        return {"recovered": False}
    transaction = read_json(journal)
    if transaction.get("format") != "AIOS-transaction/1" or transaction["state"] not in {"prepared", "committed"}:
        raise ValueError("Invalid transaction journal")
    pending = []
    seen = set()
    for item in transaction["files"]:
        path = workspace_path(root, item["path"])
        relative = path.relative_to(root).as_posix()
        if (not relative.startswith((".ai-os/memory/tasks/", ".ai-os/memory/semantic/knowledge/"))
                and relative != ".ai-os/memory/episodic/decisions.jsonl") or path in seen:
            raise ValueError("Invalid recovery target")
        seen.add(path)
        before, after = decoded(item["before"]), decoded(item["after"])
        if state(path) not in (before, after):
            raise ValueError("Recovery found an outside edit; preserve the journal for review")
        pending.append((path, after if transaction["state"] == "committed" else before))
    for path, raw in pending:
        if raw is None:
            path.unlink(missing_ok=True)
        else:
            atomic_write(path, raw)
    journal.unlink()
    return {"recovered": True, "state": transaction["state"]}


def recover(root):
    with memory_lock(root):
        return recover_locked(root)


def transact(root, changes):
    journal = workspace_path(root, JOURNAL)
    records = [{"path": path.relative_to(root).as_posix(), "before": encoded(before), "after": encoded(after)}
               for path, (before, after) in changes.items()]
    transaction = {"format": "AIOS-transaction/1", "state": "prepared", "files": records}
    atomic_write(journal, canonical_json(transaction))
    try:
        for path, (before, after) in changes.items():
            if state(path) != before:
                raise ValueError("Memory changed outside the transaction; no overwrite allowed")
            atomic_write(path, after)
        transaction["state"] = "committed"
        atomic_write(journal, canonical_json(transaction))
    except Exception:
        recover_locked(root)
        raise
    journal.unlink()


def promote(root, proposal):
    proposal = read_json(workspace_path(root, proposal))
    with memory_lock(root):
        if workspace_path(root, JOURNAL).exists():
            raise ValueError("Recover the unfinished transaction first")
        task = memory_path(root, proposal["task"], "tasks")
        before = task.read_bytes()
        if digest(before) != proposal["task_sha256"]:
            raise ValueError("Task changed since the proposal was reviewed")
        text = before.decode("utf-8")
        entries = {match.group(1): match for match in ENTRY.finditer(text)}
        if len(entries) != len(list(ENTRY.finditer(text))):
            raise ValueError("Duplicate task entry IDs")
        changes, selected = {}, set()
        promotions = proposal["promotions"]
        if not isinstance(promotions, list) or not promotions:
            raise ValueError("Select at least one accepted entry")
        for item in promotions:
            identity = item["entry_id"]
            if item.get("accepted") is not True or identity in selected or identity not in entries:
                raise ValueError("Promotion needs unique, explicitly accepted task entries")
            entry = entries[identity]
            if UNRESOLVED.search(entry.group(2)):
                raise ValueError("Unresolved work cannot become semantic memory")
            validate_evidence(root, item["evidence"])
            destination = memory_path(root, item["destination"], "semantic/knowledge")
            previous = state(destination)
            if (digest(previous) if previous is not None else None) != item["destination_sha256"]:
                raise ValueError("Destination changed since review")
            staged = changes.get(destination, (previous, previous or b""))[1]
            if ("AIOS-ENTRY: " + identity).encode() in staged:
                raise ValueError("Entry already promoted to this destination")
            provenance = canonical_json({"task": proposal["task"], "entry_id": identity,
                                         "evidence": item["evidence"]}).decode("utf-8")
            changes[destination] = (previous, staged + ("\n" + entry.group(0) + "\n<!-- AIOS-PROVENANCE: "
                                                       + provenance + " -->\n").encode("utf-8"))
            selected.add(identity)
        # Drain only selected blocks; preserve all other bytes, including active plans and TODOs.
        remaining = text
        for identity in selected:
            remaining = remaining.replace(entries[identity].group(0), "", 1)
        changes[task] = (before, remaining.encode("utf-8"))
        add_decision(root, changes, "Promoted task entries: " + ", ".join(sorted(selected)),
                     "Accepted entries with fresh verification evidence")
        transact(root, changes)
        return {"promoted": sorted(selected)}


def add_decision(root, changes, what, why):
    log = workspace_path(root, ".ai-os/memory/episodic/decisions.jsonl")
    before = state(log)
    decision = {"ts": datetime.now(timezone.utc).isoformat(), "type": "decision", "what": what,
                "why": why, "files": [path.relative_to(root).as_posix() for path in changes]}
    prefix = before or b""
    if prefix and not prefix.endswith(b"\n"):
        prefix += b"\n"
    changes[log] = (before, prefix + canonical_json(decision) + b"\n")


def amend(root, proposal):
    proposal = read_json(workspace_path(root, proposal))
    with memory_lock(root):
        if workspace_path(root, JOURNAL).exists():
            raise ValueError("Recover the unfinished transaction first")
        if proposal.get("accepted") is not True:
            raise ValueError("Amendment needs an explicitly accepted review")
        path = memory_path(root, proposal["destination"], "semantic/knowledge")
        before = path.read_bytes()
        if digest(before) != proposal["destination_sha256"]:
            raise ValueError("Destination changed since review")
        validate_evidence(root, proposal["evidence"])
        text, old = before.decode("utf-8"), proposal["old_text"]
        if not isinstance(old, str) or not old or text.count(old) != 1:
            raise ValueError("Amendment must identify exactly one existing passage")
        new = context_item(root, proposal["replacement_file"], "reviewed correction")["content"] if proposal["replacement_file"] else ""
        if UNRESOLVED.search(new):
            raise ValueError("Unresolved work cannot become semantic memory")
        after = text.replace(old, new, 1)
        provenance = canonical_json({"evidence": proposal["evidence"], "replaces_sha256": digest(old.encode("utf-8"))})
        after += "\n<!-- AIOS-AMENDMENT: " + provenance.decode("utf-8") + " -->\n"
        changes = {path: (before, after.encode("utf-8"))}
        add_decision(root, changes, "Amended semantic memory", "Reviewed correction or retraction with fresh evidence")
        transact(root, changes)
        return {"amended": path.relative_to(root).as_posix()}
