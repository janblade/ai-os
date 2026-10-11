"""Idempotent hook merging; host trust and permissions remain host-owned."""

import re
import subprocess

from storage import atomic_write, canonical_json, read_json, workspace_path


def install_hooks(root, host, template):
    if host == "claude":
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True, check=False)
        version = re.search(r"\b(\d+)\.(\d+)\.(\d+)\b", result.stdout)
        if result.returncode or not version or tuple(map(int, version.groups())) < (2, 1, 295):
            raise ValueError("Claude Code 2.1.295+ is required for fail-closed gates")
    incoming = read_json(template)
    expected = {"SessionStart", "SubagentStart", "PreToolUse", "Stop"}
    if set(incoming.get("hooks", {})) != expected:
        raise ValueError("Expected the four AI-OS host hook events")
    for event, groups in incoming["hooks"].items():
        if not isinstance(groups, list) or len(groups) != 1 or len(groups[0]["hooks"]) != 1:
            raise ValueError("Expected one AI-OS handler per event")
        handler = groups[0]["hooks"][0]
        if host == "claude":
            command = 'bash "${CLAUDE_PROJECT_DIR}/.ai-os/scripts/session-start-hook.sh"'
            if event != "SessionStart":
                command += " " + event
            if handler.get("command") != command or handler.get("type") != "command":
                raise ValueError("Unrecognized Claude hook command")
            if event in {"PreToolUse", "Stop"} and handler.get("onFailure") != "block":
                raise ValueError("Claude gates must fail closed")
        elif host == "codex":
            tail = ' "$(git rev-parse --show-toplevel)/.ai-os/scripts/ai_os.py" hook ' + event + ' --host codex'
            if (handler.get("command") != "python3" + tail or handler.get("commandWindows") != "python" + tail
                    or handler.get("type") != "command"):
                raise ValueError("Unrecognized Codex hook command")
        else:
            raise ValueError("Unsupported host")
    name = ".claude/settings.json" if host == "claude" else ".codex/hooks.json"
    path = workspace_path(root, name)
    before = path.read_bytes() if path.exists() else None
    config = read_json(path) if before is not None else {}
    hooks = config.setdefault("hooks", {})
    marker = "/.ai-os/scripts/session-start-hook.sh" if host == "claude" else "/.ai-os/scripts/ai_os.py"
    for event, groups in incoming["hooks"].items():
        existing = hooks.setdefault(event, [])
        found = False
        for group in existing:
            owned = [handler for handler in group["hooks"] if marker in handler.get("command", "")]
            if owned:
                group["hooks"] = [handler for handler in group["hooks"] if handler not in owned] + groups[0]["hooks"]
                # Preserve a user's narrowed subagent matcher; refresh framework default matchers.
                if event != "SubagentStart" and "matcher" in groups[0]:
                    group["matcher"] = groups[0]["matcher"]
                found = True
        if not found:
            existing.extend(groups)
    after = canonical_json(config) + b"\n"
    if (path.read_bytes() if path.exists() else None) != before:
        raise ValueError("Host settings changed during merge; retry after review")
    if after != before:
        atomic_write(path, after)
    return {"settings": name, "changed": after != before,
            "host_review_required": host == "codex"}
