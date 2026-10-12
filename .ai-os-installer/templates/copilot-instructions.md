# AI OS Framework Active

This project is governed by the AI OS Framework. If your environment can read and follow
`.ai-os/BOOT.md`, use the validated startup pack if already supplied; otherwise read it — everything below is a fallback
summary so this project stays governed correctly even on hosts that only read this file.

## Minimum Contract (applies even if you never open BOOT.md)

1. **Kernel read-only by default**: kernel files and hook code/settings require explicit
   human authorization for named files or a bounded maintenance scope. Ordinary feature
   requests do not grant governance edits. Honor existing scoped authorization without a
   magic phrase or repeated approval. Direct file/patch tools cannot bypass protection;
   apply approved maintenance through trusted host controls or an operator terminal,
   log changes, then start a new session. Host instructions always take precedence.
2. **Before writing code**: check for hardcoded secrets, obvious injection risk, and
   unsafe functions (`eval`, `os.system`) in what you're about to write. Never print
   credentials to chat or logs.
3. **Before a substantive task**: use `.ai-os/scripts/ai_os.py pack` with only relevant `--skill`/`--file` selections. Resolve task filenames with `.ai-os/scripts/ai_os.py task --name <original identity>`; never sanitize branch names manually. Then read `.ai-os/memory/semantic/project_knowledge.md` for
   confirmed project facts, and check `.ai-os/memory/tasks/` for an open task file — every
   branch gets one, including main (ask what to call it if there's no git identity and none
   exists yet) — for in-progress working notes.
4. **After a significant decision or action**: append one line to
   `.ai-os/memory/episodic/decisions.jsonl`:
   `{"ts": "<ISO 8601>", "type": "decision|action", "what": "...", "why": "..."}`
5. **Don't create IDE-specific planning artifacts** (`task.md`, `implementation_plan.md`,
   `walkthrough.md`). Use `.ai-os/memory/tasks/` instead — one filesystem of record, not
   several competing ones. If your host creates one anyway (some IDEs force this via their
   own planning-mode hook, outside your control) — don't leave it orphaned: ask the user
   whether to absorb its content into the current task file, then ask before deleting the
   original.

## Full Protocol

If you can execute a multi-file boot sequence: read `.ai-os/BOOT.md` and follow its §2
Boot Sequence. That file is a compact hot-core with pointers to detailed rules, skills,
and commands — read those linked files only when their trigger condition applies, not
speculatively.

Commands (when supported): `> OS_COMMAND [NAME] [--param=value]`. Full list in
`.ai-os/commands/index.json`.
