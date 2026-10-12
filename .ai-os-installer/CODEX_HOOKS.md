# Optional Codex context hooks

Opt-in startup context only. Keep the existing root AGENTS.md bridge. This adapter reads
BOOT.md, ultimate_rules.md, and the task selected by task_identity.py; it never writes
memory, validates mutations, grants permission, or blocks Stop. Base governance applies.

## Install or update

1. Copy scripts/ with the framework, including task_identity.py and codex-context-hook.py.
   Python 3.8+ and a local Codex host supporting the documented hook fields are required.
2. Merge templates/codex-hooks.json into the project's .codex/hooks.json only after the
   user opts in. Match an existing AI-OS handler by codex-context-hook.py and update that
   handler in place; preserve unrelated groups, custom matcher scope and disabled flags.
   If absent, add one group per event. Do not also add equivalent inline config.toml hooks.
3. Commands locate the script from the Git root, including when launched in a subdirectory.
   Windows commandWindows is for PowerShell with python and Git on PATH; POSIX uses python3. It sets console output to UTF-8 first so non-ASCII project paths from `git rev-parse` survive Windows PowerShell 5.1.
   For non-Git workspaces, replace the script location with a shell-quoted absolute path.
4. Inspect /hooks and explicitly review/trust the new or changed definitions. Never bypass
   hook trust automatically. Unsupported hosts retain the bridge and manual file reads.
5. Run each command manually, check its JSON, then verify startup/resume/compact and a
   subagent in the actual host. Disabling/removing these two handlers rolls back the add-on.

## Output and failure behavior

The adapter caps each input and the combined context at 64 KiB, never silently truncating
rules. additionalContextLimit=0 avoids host preview spilling within that local bound.
An oversized/unreadable governance source returns a warning asking for explicit reads.
Task lookup failure warns and retains governance. Errors do not produce deny/stop outputs.
There are no locks, journals, retained snapshots, or per-tool work. Repeated startup events
repeat context; this is not a token optimization or technical kernel security boundary.

## Host contract and validation

[Official Codex hooks documentation](https://learn.chatgpt.com/docs/hooks) documents
project .codex/hooks.json discovery, trust review, SessionStart/SubagentStart, source
matchers, JSON additionalContext, commandWindows, timeout, and additionalContextLimit.
No shell/onFailure field or guessed minimum Codex release is used. Command hooks require
local orchestration; this template does not claim Codex Cloud support.

Test commands: python -B -m unittest discover -s tests -v. Tested on Windows/Python 3.12
with direct Python, PowerShell and Git Bash launchers, and on Ubuntu under WSL with
POSIX shell commands. Native Codex context delivery and macOS remain unverified;
launcher tests alone do not establish delivery.
