# First-Boot Protocol

> Loaded only when `BOOT.md` §10 triggers: `manifest.json.project_name` is empty.
> If `memory/semantic/project_knowledge.md` already contains real project data
> despite the empty manifest, do NOT run the wizard — just ask the user:
> *"Your manifest is unconfigured, but I see existing project memory. What
> should I set as the project name?"* and update `manifest.json` directly.

Otherwise, run the full bootstrap:

## Step 1: Verify Directory Structure
Ensure the complete `.ai-os/` tree exists (see `kernel/integrity.md`). Create any missing directories or files from defaults.

## Step 2: First-Boot Wizard
Ask the user, one at a time:
1. "What is this project called?" → `manifest.json.project_name`
2. "What kind of project is this?"
   - **Hobby** — personal/learning. Lightweight governance, maximum speed.
   - **Startup** — production-bound but moving fast. Balanced.
   - **Enterprise** — team-based, compliance-aware. Full audit trail.
   - **Critical** — financial/medical/infra. Maximum safety, minimum autonomy.
   - **Auto-detect** — let the OS determine from project signals.
3. "Any project-specific rules or constraints?" → append to `rules/ultimate_rules.md`'s `<!-- PROJECT_RULES_START -->` block.

## Step 3: Perception Scan
Run BOOT.md §2 step 2 (genome detection / archetype resolution).

## Step 4: Initialize Memory
Create missing memory files with empty/default content. Never overwrite existing memory. Write the first `last_session.json` entry.

## Step 5: Report

```
╔══════════════════════════════════════════════╗
║          AI OS v2.8.0 — First Boot          ║
╠══════════════════════════════════════════════╣
║ Project:    {name}                          ║
║ Archetype:  {archetype}                     ║
║ Stack:      {detected languages/frameworks} ║
║ Skills:     {count} core skills loaded      ║
║ Commands:   {count} commands available      ║
║                                             ║
║ Type: > OS_COMMAND HELP for commands        ║
║ Type: > OS_COMMAND STATUS for health        ║
╚══════════════════════════════════════════════╝
```
