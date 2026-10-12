"""Claude Code and Codex hooks sharing the command-line context assembler."""

import json
import re

from context import assemble_pack, diff_packs, load_snapshot, render_pack, save_snapshot
from memory import ENTRY, JOURNAL
from storage import RUNTIME, atomic_write, canonical_json, digest, memory_lock, read_json, workspace_path


KERNEL_FILES = {".ai-os/BOOT.md", ".ai-os/manifest.json", ".claude/settings.json",
                ".claude/settings.local.json", ".codex/hooks.json", ".codex/config.toml"}
KERNEL_DIRECTORIES = (".ai-os/kernel", ".ai-os/rules", ".ai-os/genome/archetypes", ".ai-os/scripts")
MANIFEST_OPERATIONAL = {"boot_count", "last_boot", "tech_stack", "evolution_history"}


def protected_path(relative):
    relative = relative.casefold()
    return relative in {name.casefold() for name in KERNEL_FILES} or any(
        relative == directory or relative.startswith(directory + "/") for directory in KERNEL_DIRECTORIES)


def protected_sources(root):
    sources = {}
    paths = [workspace_path(root, name) for name in sorted(KERNEL_FILES)]
    for name in KERNEL_DIRECTORIES:
        directory = workspace_path(root, name)
        if directory.exists():
            for candidate in sorted(directory.rglob("*")):
                path = workspace_path(root, candidate.relative_to(root).as_posix())
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                    paths.append(path)
    for path in paths:
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            raw = path.read_bytes()
            if relative.casefold() == ".ai-os/manifest.json":
                value = read_json(path)
                raw = canonical_json({key: item for key, item in value.items() if key not in MANIFEST_OPERATIONAL})
            sources[relative] = digest(raw)
    return sources


def check_protected_sources(pointer, sources):
    if read_json(pointer).get("protected_sources") != sources:
        raise ValueError("Kernel or hook configuration changed; review scoped maintenance through host controls and start a new session")


def mutation_text(before, tool, data):
    if tool == "Write":
        return data["content"]
    after = before
    for edit in data["edits"] if tool == "MultiEdit" else [data]:
        old, new = edit["old_string"], edit["new_string"]
        if not old:
            raise ValueError("Edits need a nonempty matching old_string")
        after = after.replace(old, new, -1 if edit.get("replace_all") else 1)
    return after


def check_path(relative):
    if protected_path(relative):
        raise ValueError("Kernel and hook edits require scoped maintenance through trusted host controls")
    if relative.startswith(".ai-os/memory/semantic/") and not relative.startswith(".ai-os/memory/semantic/generated/"):
        raise ValueError("Durable semantic writes require reviewed proposals; use the memory CLI")
    if relative.startswith(RUNTIME + "/"):
        raise ValueError("Runtime state is managed by the AI-OS CLI")


def decision(reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


def check_edit(root, tool, data):
    if tool == "apply_patch":
        command = data.get("command")
        if not isinstance(command, str):
            raise ValueError("Patch hook input needs a command string")
        paths = re.findall(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$", command, re.MULTILINE)
        if not paths:
            raise ValueError("Patch has no supported file operations")
        for name in paths:
            path = workspace_path(root, name.strip())
            relative = path.relative_to(root).as_posix().casefold()
            check_path(relative)
            # shortcut: protect whole tasks containing identified notes; add surgical patch support when needed.
            if relative.startswith(".ai-os/memory/tasks/") and path.exists() and ENTRY.search(path.read_text(encoding="utf-8")):
                raise ValueError("Use the memory CLI for a task containing identified notes")
        return
    if tool not in {"Write", "Edit", "MultiEdit"}:
        return
    name = data.get("file_path")
    if not isinstance(name, str) or not name:
        raise ValueError("File mutation needs a workspace path")
    path = workspace_path(root, name)
    relative = path.relative_to(root).as_posix().casefold()
    if relative == ".ai-os/manifest.json":
        before = read_json(path)
        after = json.loads(mutation_text(path.read_text(encoding="utf-8-sig"), tool, data))
        if not isinstance(after, dict) or ({key: value for key, value in before.items() if key not in MANIFEST_OPERATIONAL}
                                         != {key: value for key, value in after.items() if key not in MANIFEST_OPERATIONAL}):
            raise ValueError("Only operational manifest fields may auto-update; other changes require scoped maintenance")
        return
    check_path(relative)
    if not relative.startswith(".ai-os/memory/tasks/") or not path.exists():
        return
    before = path.read_text(encoding="utf-8")
    after = mutation_text(before, tool, data)
    old_entries = {match.group(1): match.group(0) for match in ENTRY.finditer(before)}
    new_entries = {match.group(1): match.group(0) for match in ENTRY.finditer(after)}
    if any(new_entries.get(key) != value for key, value in old_entries.items()):
        raise ValueError("Identified notes must be preserved; use selective promotion to drain them")


def session_pointer(root, body):
    session = body.get("session_id")
    agent = body.get("agent_id", "")
    if not isinstance(session, str) or not session or not isinstance(agent, str):
        raise ValueError("Hook input needs a session identity")
    key = digest(canonical_json([body.get("ai_os_host", "claude"), session, agent]))
    return workspace_path(root, RUNTIME + "/sessions/" + key + ".json")


def hook(root, event, body):
    if not isinstance(body, dict) or body.get("hook_event_name") != event:
        raise ValueError("Hook event does not match its input")
    if event == "Stop":
        with memory_lock(root):
            pointer = session_pointer(root, body)
            if pointer.exists():
                check_protected_sources(pointer, protected_sources(root))
            if workspace_path(root, JOURNAL).exists():
                return {"decision": "block", "reason": "Recover the unfinished AI-OS memory transaction before finishing"}
        return {}
    if event not in {"SessionStart", "SubagentStart", "PreToolUse"}:
        raise ValueError("Unsupported hook event")
    pointer = session_pointer(root, body)
    with memory_lock(root):
        sources = protected_sources(root)
        if pointer.exists():
            check_protected_sources(pointer, sources)
        parent = session_pointer(root, {**body, "agent_id": ""})
        if parent != pointer and parent.exists():
            check_protected_sources(parent, sources)
        pack = assemble_pack(root)
        if event != "PreToolUse":
            snapshot = save_snapshot(root, pack)
            atomic_write(pointer, canonical_json({"snapshot": snapshot.relative_to(root).as_posix(), "protected_sources": sources}))
            return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": render_pack(pack)}}
        if not pointer.exists():
            return decision("No validated AI-OS startup context; restart the session after checking hook setup")
        previous = load_snapshot(workspace_path(root, read_json(pointer)["snapshot"]))
        check_edit(root, body["tool_name"], body["tool_input"])
        delta = diff_packs(previous, pack)
        if previous["task"] == pack["task"] and not any(delta.values()):
            return {}  # Ordinary tool calls do not repeat governance or unchanged task text.
        changed = set(delta["added"]) | {entry["id"] for entry in delta["changed"]}
        message = "AI-OS context update supersedes prior versions of these items. "
        message += canonical_json({"task": pack["task"], "framework_version": pack["framework_version"],
                                   "removed": delta["removed"]}).decode("utf-8")
        for item in pack["items"]:
            if item["id"] in changed:
                message += "\n" + canonical_json(item).decode("utf-8")
        snapshot = save_snapshot(root, pack)
        atomic_write(pointer, canonical_json({"snapshot": snapshot.relative_to(root).as_posix(), "protected_sources": sources}))
        return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": message}}
