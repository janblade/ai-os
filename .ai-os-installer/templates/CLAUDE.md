# AI OS Framework Active

This project is governed by the AI OS Framework. If your environment can read and follow
`.ai-os/BOOT.md`, do that now for the full protocol — everything below is a fallback
summary so this project stays governed correctly even on hosts that only read this file.

## Minimum Contract (applies even if you never open BOOT.md)

1. **Kernel space is read-only**: never edit `.ai-os/BOOT.md`, `.ai-os/manifest.json`,
   `.ai-os/kernel/`, `.ai-os/rules/`, or `.ai-os/genome/archetypes/` unless the user's
   message contains the literal phrase `KERNEL OVERRIDE AUTHORIZED`.
2. **Before writing code**: check for hardcoded secrets, obvious injection risk, and
   unsafe functions (`eval`, `os.system`) in what you're about to write. Never print
   credentials to chat or logs.
3. **Before a substantive task**: read `.ai-os/memory/semantic/project_knowledge.md` for
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
