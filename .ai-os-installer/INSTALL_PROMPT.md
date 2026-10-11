# AI OS Framework Installer

Hello! If you are reading this, the user has asked you to install the **AI OS Framework** into this workspace. 
You are going to act as the Agentic Installer. Your job is to merge the necessary boot instructions into the user's existing workspace without destroying any of their existing rules.

## ⚡ Execute Independent Steps in Parallel
Wherever a step below lists multiple file operations that don't depend on each other's
output (different target files, no ordering requirement), issue them as parallel/batched
tool calls instead of one round-trip per file — this is the main lever for a fast install.
Serialize only where a step explicitly says one action must precede another (e.g. a
directory must exist before something is written into it).

## 🛑 Pre-Flight Safety Check
Before proceeding, check if the host AI environment's bridge file (e.g., `.cursor/rules/ai-os.md`, `.windsurfrules`, `.agents/AGENTS.md`) is already configured with AI OS boot instructions. If it is already configured, **STOP IMMEDIATELY**. Inform the user: *"The AI OS Framework is already installed here. Please use the UPDATE_PROMPT.md instead to prevent memory loss and duplicate rules."* Do not execute any further steps. (Fallback case: if `.ai-os/` already exists in the project but the bridge files do not — e.g. someone copied it in manually before this ran — record that this installation pre-existed, skip Step 1's copy, and proceed from Step 2. Also SKIP Step 4 entirely: missing bridges do not authorize resetting existing memory, rules, or manifest settings. Use UPDATE_PROMPT.md for framework upgrades.)

## Step 1: Locate & Copy the Framework Kernel
You are being run from wherever the user downloaded/cloned MaiKS — this file lives
inside that package's `.ai-os-installer/` folder, a sibling of its `.ai-os/` folder. That
download location does NOT need to already be inside the project; the user should not have
copied anything in manually before starting this conversation. You do the copying now.
1. Determine the downloaded package's root (the parent of the `.ai-os-installer/` folder
   this file lives in). Ask the user for the path if you can't resolve it from how you were
   invoked.
2. Copy that package's `.ai-os/` folder into the root of the CURRENT project — the only
   folder that needs to land there. Exclude `memory/runtime/` and `__pycache__/`: snapshots, evidence, journals, locks, and bytecode are private local state, never install templates.
3. Do NOT copy `.ai-os-installer/` itself into the project. It stays in the downloaded
   package. Nothing else is needed from it this session, and a future upgrade uses a freshly
   downloaded package's `UPDATE_PROMPT.md` the same way — not a copy left behind here.

## Step 2: Detect Host AI Environment
Do not guess your environment. Use your file/directory listing tools to check the workspace root:
- If a `.cursor` directory exists, you are in **Cursor**.
- If a `.windsurf` directory or `.windsurfrules` exists, you are in **Windsurf**.
- If neither exists, ask the user: *"Which AI assistant are you using? (Cursor, Windsurf, Claude Code, Codex, GitHub Copilot, Gemini/Antigravity)"*

## Step 3: Merge Bridge Files (Do Not Overwrite!)
Depending on the host environment, find the corresponding template file in `.ai-os-installer/templates/`.
Read the template. Then, **append** its exact text to the bottom of the user's existing bridge file.
- **Cursor:** Create `.cursor/rules/ai-os.mdc` with this frontmatter prepended so it auto-attaches:
  ```
  ---
  alwaysApply: true
  ---
  ```
  followed by the `cursor-rules.md` template text. (Plain `.cursor/rules/ai-os.md` without frontmatter may not auto-load in current Cursor versions — use `.mdc`.)
- **Windsurf:** Append to `.windsurfrules`.
- **Claude Code:** Append the `CLAUDE.md` bridge. Require Python 3.10+ and Claude Code
  2.1.295+ on PATH. Run:
  `python .ai-os/scripts/ai_os.py install-hooks --host claude --template <package-root>/.ai-os-installer/templates/claude-code-hooks.json`
  The helper checks Claude's actual version and merges startup, subagent, mutation, and
  completion hooks without replacing unrelated settings. No silent fallback when runtime
  requirements fail. Verify `/hooks` lists all four events after restarting the host.
- **Codex:** Append the root `AGENTS.md` bridge once, then run:
  `python .ai-os/scripts/ai_os.py install-hooks --host codex --template <package-root>/.ai-os-installer/templates/codex-hooks.json`
  Python 3.10+ and a host with hooks support are required. The template resolves the Git
  root; Windows commands expect PowerShell and `python` on PATH. For non-Git projects,
  adapt commands to shell-quoted absolute script paths after installation. Review/trust
  the project hooks in Codex `/hooks`; never bypass trust automatically. Codex launch
  errors/timeouts may fail open, so retain native host permissions. Both providers use
  the same reproducible AI-OS pack; full rule/skill files load only when selected.
- **GitHub Copilot:** Append to `.github/copilot-instructions.md`.
- **Gemini / Antigravity:** Append to `.agents/AGENTS.md` and copy `skills.json` to `.agents/skills.json`.
- **Root `AGENTS.md`:** Also create/append to a root-level `AGENTS.md` regardless of the above — it's the emerging cross-tool convention (Codex, Jules, and others read it directly), and costs nothing extra for hosts that ignore it.

**Fallback:** If you do not have the tool capabilities to create or edit files, do not apologize. Simply print the exact text of the template into the chat in a markdown block, and ask the user to paste it into their bridge file.

## Step 4: Purge Framework Meta-Memory & Reset Manifest
**Only for a fresh Step 1 copy into a project with no prior `.ai-os/`. If it pre-existed, skip this whole step regardless of bridge or manifest state.**

Since Step 1 copied `.ai-os/` directly from the MaiKS package, it still contains memory logs and genome details from the framework's own development. This will pollute the user's new project.
Using your file editing tools, reset the following files to prevent context pollution. Items
1–7 each target an independent file — batch them as parallel tool calls. Items 8 and 9 both
touch `commands/index.json` and `registry/index.json`; do those two together in one pass per
shared file rather than editing the same file twice.
1. **`.ai-os/memory/semantic/project_knowledge.md`**: Overwrite with the default Indexed Knowledge Index template:
   ```markdown
   # Project Knowledge Index

   > This file acts as the primary index for the project's semantic knowledge base.
   > To prevent git merge conflicts between multiple developers and concurrent branches,
   > institutional knowledge is split into specialized sub-files linked below.

   ---

   ## Knowledge Domains

   - [Architecture Overview](knowledge/architecture_overview.md) — System architecture, module boundaries, and host integrations.
   - [Conventions & Patterns](knowledge/conventions_patterns.md) — Coding standards, security rules, and testing patterns.
   - [Known Gotchas](knowledge/known_gotchas.md) — Pitfalls, failure modes, and environment workarounds.
   ```
2. **`.ai-os/memory/semantic/knowledge/` sub-files**: Ensure `.ai-os/memory/semantic/knowledge/` exists. Reset `architecture_overview.md`, `conventions_patterns.md`, and `known_gotchas.md` to baseline header files.
3. **`.ai-os/memory/episodic/decisions.jsonl`, `.ai-os/memory/episodic/sessions.jsonl`, `.ai-os/memory/episodic/decisions.archive.jsonl`** (if present): Empty the contents of these files. Reset `.ai-os/memory/episodic/last_session.json` to `{"session_id": null, "started": null, "ended": null, "summary": null, "next_up": null}`.
4. **`.ai-os/memory/tasks/`, `.ai-os/memory/archived_tasks/`, and `.ai-os/memory/plans/`**: Delete every `.md` file in all three directories except `.keep` — including `plans/_summary.md` if the distributing repo shipped one. MaiKS's own development task and plan files (anything not matching a template default) must never leak into a fresh install — this was a real bug (a stray `EP-8-thinking-protocol.md` shipped in the repo before EP-23 fixed it).
5. **`.ai-os/progress.md`**: Clear out the decisions and evolution proposals sections.
6. **`.ai-os/manifest.json`**: Reset `project_name` to `""`, reset `project_archetype` to `"auto"`, reset `boot_count` to `0`, reset `last_boot` to `null`, clear the `tech_stack` object (`{}`), and reset `evolution_history` to `{"total_evolutions": 0, "last_evolution": null}` — MaiKS's own evolution count and archetype must not carry into a new project. A non-`"auto"` archetype (e.g. this repo's own `"startup"`) skips `BOOT.md` §2 step 2's detection entirely and gets used as-is with no chance to ask — that was a real bug: fresh installs copying this repo's own `.ai-os/` folder silently inherited MaiKS's own archetype instead of ever being asked. Leave `ai_os_version` and `installed_skills` as-is; those describe the framework build being installed, not the project. Also reset `.ai-os/genome/project_genome.json` indicators to baseline defaults so the **First-Boot Wizard** in `BOOT.md` §10 will correctly trigger.
7. **`.ai-os/rules/ultimate_rules.md`'s Project-Specific Addendum**: Reset the content between `<!-- PROJECT_RULES_START -->` and `<!-- PROJECT_RULES_END -->` back to the single placeholder line `<!-- Add project-specific rules here -->`, discarding whatever MaiKS's own copy had there. `kernel/bootstrap.md` Step 2.3 writes a new project's own rules into this exact block on first boot — if the block isn't purged here, a fresh install inherits the *distributing* project's rules as if they were its own. This is the install-time counterpart to `UPDATE_PROMPT.md`'s Step 3a, which does the opposite (preserve, never purge) for an *existing* install being upgraded — the two are not interchangeable, don't copy one's logic into the other's context.
8. **`EVOLVE_BENCHMARK` (project-only command)**: This command is a rule specific to MaiKS's own dev repo (see the Addendum text just reset in step 7 — it compares *this framework* against competing AI agent frameworks, which only makes sense for the repo that builds MaiKS, not a project that merely installed it). Remove its entry from `.ai-os/commands/index.json`'s command list, and remove the string `"EVOLVE_BENCHMARK"` from `core.evolution.sk`'s `commands` array in `.ai-os/registry/index.json`. Leave the rest of `core.evolution.sk` (including its `SKILL.md`, which still documents the command for MaiKS's own reference) untouched — only the two registrations that make it invocable are purged.
9. **`RELEASE` (project-only command)**: Same rationale and same treatment as item 8. `RELEASE` is MaiKS's own commit-and-push-to-`main` gate for an applied evolution (one commit per EP, no PR) — an installed project commits its evolutions per its own VCS conventions, not this procedure. Remove its entry from `.ai-os/commands/index.json`'s command list, remove the string `"RELEASE"` from `core.evolution.sk`'s `commands` array in `.ai-os/registry/index.json`, and remove the `"release"` and `"ship"` keys from `.ai-os/commands/aliases.json`. Leave `core.evolution.sk/SKILL.md`'s `### RELEASE` section in place (documentation only, harmless once unregistered) and leave the `EVOLVE_APPLY` step 6 pointer to it (it already reads "in an installed project, follow the project's own VCS conventions").
10. **Project-only procedural memory (EP-75)**: Same non-inheritance class as items 8–9, one level down — a *playbook or workflow entry* about MaiKS's own dev process, rather than a whole command. (a) In `.ai-os/memory/procedural/playbooks.md`, delete any `## Playbook:` section whose heading line is immediately followed by a `**Project-only**` line — remove through the next `## Playbook:` heading or end of file, whichever comes first. (b) In `.ai-os/memory/procedural/workflows.json`, remove any entry in the `workflows` array where `"project_only": true`. Leave every other playbook/workflow untouched — these are generic starting templates meant for any project, not MaiKS-specific.
11. **`PUBLISH` (project-only command, EP-76)**: Same rationale and same treatment as items 8–9. `PUBLISH` is MaiKS's own mechanism for shipping this repo's `.ai-os/`/`.ai-os-installer/` to the separate public `ai-os` distribution repo — an installed project has no such second repo to publish to. Remove its entry from `.ai-os/commands/index.json`'s command list, remove the string `"PUBLISH"` from `core.evolution.sk`'s `commands` array in `.ai-os/registry/index.json`, and remove the `"publish"` key from `.ai-os/commands/aliases.json`. Leave `core.evolution.sk/SKILL.md`'s `### PUBLISH` section in place (documentation only, harmless once unregistered).


## Step 5: Verify Integrity & Gitignore
1. Check that the `.ai-os/` directory exists in the root of the workspace — confirming Step 1's copy actually landed. If it does not, retry Step 1 rather than asking the user to copy it manually.
2. Open the user's `.gitignore` file (create it if it doesn't exist) and append the following lines to prevent merge-conflict hell from highly active AI files:
```text
# AI OS Ephemeral Memory
.ai-os/memory/episodic/sessions.jsonl
.ai-os/memory/episodic/last_session.json
.ai-os/memory/episodic/session_override.json
.ai-os/memory/runtime/
.ai-os/progress.md
```
Do **not** add `decisions.jsonl` or `decisions.archive.jsonl` to this list — those are the
permanent audit trail and are meant to be shared/committed, unlike the per-machine session
log above them.

## Step 6: Boot!
Read `.ai-os/BOOT.md` and begin executing the Initialization Checklist as the newly installed AI OS Kernel. Greet the user with the boot status banner!
