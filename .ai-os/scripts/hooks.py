"""Claude Code and Codex hooks sharing the command-line context assembler."""

import re

from context import assemble_pack, diff_packs, load_snapshot, render_pack, save_snapshot
from memory import ENTRY, JOURNAL
from storage import RUNTIME, atomic_write, canonical_json, digest, memory_lock, read_json, workspace_path


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
            relative = path.relative_to(root).as_posix()
            if relative.startswith((".ai-os/memory/semantic/", RUNTIME + "/")):
                raise ValueError("Memory and runtime patches require the reviewed memory CLI")
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
    relative = path.relative_to(root).as_posix()
    if relative.startswith(".ai-os/memory/semantic/"):
        raise ValueError("Semantic writes require reviewed promote proposals; use the memory CLI")
    if relative.startswith(RUNTIME + "/"):
        raise ValueError("Runtime state is managed by the AI-OS CLI")
    if not relative.startswith(".ai-os/memory/tasks/") or not path.exists():
        return
    before = path.read_text(encoding="utf-8")
    after = before
    if tool == "Write":
        after = data["content"]
    else:
        edits = data["edits"] if tool == "MultiEdit" else [data]
        for edit in edits:
            old, new = edit["old_string"], edit["new_string"]
            if not old:
                raise ValueError("Task edits need a nonempty matching old_string")
            after = after.replace(old, new, -1 if edit.get("replace_all") else 1)
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
            if workspace_path(root, JOURNAL).exists():
                return {"decision": "block", "reason": "Recover the unfinished AI-OS memory transaction before finishing"}
        return {}
    if event not in {"SessionStart", "SubagentStart", "PreToolUse"}:
        raise ValueError("Unsupported hook event")
    pointer = session_pointer(root, body)
    with memory_lock(root):
        pack = assemble_pack(root)
        if event != "PreToolUse":
            snapshot = save_snapshot(root, pack)
            atomic_write(pointer, canonical_json({"snapshot": snapshot.relative_to(root).as_posix()}))
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
        message += canonical_json({"task": pack["task"], "removed": delta["removed"]}).decode("ascii")
        for item in pack["items"]:
            if item["id"] in changed:
                message += "\n" + canonical_json(item).decode("ascii")
        snapshot = save_snapshot(root, pack)
        atomic_write(pointer, canonical_json({"snapshot": snapshot.relative_to(root).as_posix()}))
        return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": message}}
