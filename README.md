# MaiKS

MaiKS is a microkernel-inspired governance layer that runs inside your project workspace. It applies rules, a pre-write security check, and persistent memory to AI coding agents (Claude Code, Codex, Antigravity/Gemini, GitHub Copilot, Cursor, Windsurf) working in your codebase.

> **Deterministic, Git-Native Memory**
> Instead of a vector database (RAG), MaiKS stores memory as plain Markdown and JSON files alongside your code, organized as a Hub (global project knowledge) and Spokes (per-branch task notes). When someone clones the repo, their AI reads the same project knowledge, decision history, and custom skills — no external database required.

---

## Key Features

*   **Microkernel Structure**: Separation between kernel space (rules, configuration) and user space (skills, memory, commands).
*   **PDCA Self-Evolution**: A Plan-Do-Check-Act lifecycle. If the AI finds a more efficient pattern, it can propose and apply upgrades to its own workflows and skills, with rollback if integrity checks fail.
*   **Flexible Agent Delegation**: The primary agent acts as a coordinator that can edit code directly, or delegate complex, multi-file work to specialized subagents if the host environment supports it.
*   **Automatic Peer Review**: A single agent grading its own work has a structural blind spot. An independent review pass — a separate reviewer subagent where the host supports it, an honestly-labeled cold self-review where it doesn't — runs by default: once per plan (or per epic story) when working a `PLAN_WRITE` plan, and on a plan-less "implement this feature" request routed there from the boot core. The pass checks five things — correctness, conventions, security, test coverage, and **ownership fit** ("would the owner of this repo merge this diff as-is, or is it in the wrong place / at the wrong abstraction / under-designed even though it works?"). Findings surface to you; it's a second opinion, not a merge gate.
*   **Pre-Mutation Security Checklist**: Before writing code, the agent runs a security checklist for hardcoded credentials, injection patterns, and unsafe functions. Like the banner below, this is an instruction the agent follows, not a host-enforced hook, and it isn't a substitute for a dedicated SAST tool (Semgrep, Snyk, etc.) in CI.
*   **Self-Healing**: Loop detection breaks out of repeated-failure cycles. When the AI fixes a non-trivial issue, it prompts you to extract the fix into a permanent playbook so the same error doesn't need re-diagnosing next time.
*   **Skill-Invocation Visibility**: Before running any command procedure — including one it matched silently from plain English — the agent prints a one-line banner (`▸ AI-OS · core.planning.sk · PLAN_BRAINSTORM`), so you can see when a framework skill is actually being used and `grep` a transcript for the full list. This is an agent self-report convention carried in the boot core, not a host-enforced hook.
*   **Perception & Stack Discovery**: Can profile your workspace (via `OS_COMMAND INFRA_DISCOVER_MODULES`) to detect tech stack drift, map sub-modules, and generate new semantic rules or custom skills based on what it finds.
*   **Idea-to-Code Scaffolding**: An `Architect` skill that walks greenfield ideas through a structured interview to a project plan, code scaffolding, and environment config.
*   **IDE Bridge Files**: Hooks into your IDE's customization system (`.agents/skills.json`, a root `AGENTS.md`, plus host-specific files like `CLAUDE.md` and Cursor's `.mdc` rules) so skills and memory are loaded into the agent's context — each bridge file carries a self-sufficient minimum contract even on hosts that never run the full boot sequence.
*   **Host-Level Kernel Gate & Native Skill Discovery (Claude Code only)**: The installer adds `permissions.ask` rules so any edit to `BOOT.md`, `kernel/`, `rules/`, or `genome/archetypes/` raises a host prompt a human must approve — a second layer under the override phrase, not a guarantee (a script that opens the file itself isn't covered). It also generates thin pointer skills in `.claude/skills/ai-os-*/` so the host discovers each registry skill natively; the pointers hold no procedure, only a link back to `registry/*/SKILL.md`. On every other host, kernel protection is still agent self-restraint and skills are still reached through `registry/index.json`.
*   **Four-Tier Memory Model**: Reduces cross-session context loss by maintaining Episodic (decisions), Semantic (project structure), Task (active branch), and Procedural (executable playbooks) memory.
*   **Hub and Spoke Task Memory**: When you switch to a feature or bugfix branch, working memory is isolated into a dedicated task file, keeping the global project knowledge file free of branch-specific noise.
*   **Dedicated Plans Folder**: Approved implementation plans are written to `.ai-os/memory/plans/` as dated standalone files (`2026-09-03-add-pkce-flow.md`), not buried in scratch task notes. `PLAN_WRITE` and the `Architect` skill both land here; execution progress is tracked as checkboxes in the plan file itself. When a host IDE force-creates its own `implementation_plan.md`, the framework offers to move it here with its structure intact rather than flattening it into notes.
*   **Epic / Story Planning**: A large initiative that splits into several independently shippable pieces is written as an *epic* — one plan file with `## Story` sections, each carrying its own acceptance criteria that feed the completion-verification gate. `PLAN_RETRO` closes an epic with a structured lessons pass (what worked, what didn't, promotion candidates) that routes through the same verify-before-promote gate as everything else — it proposes, it doesn't write project memory directly. Ordinary single-feature work stays a flat plan; the epic form only triggers on genuine multi-piece scope.
*   **Verified Memory Promotion**: Task notes are deliberately unscrutinized working memory — half-formed ideas and dead ends are expected. Before anything gets promoted into permanent, cross-session semantic memory, it's checked two ways: is the claim still factually true against the current code, *and* was the underlying change actually accepted (not still buggy, mid-revision, or awaiting your sign-off)? A description of a bug that's still in the code is a true statement and a bad thing to remember as "how it works."

## Token Economics

**"Won't reading the entire framework on every boot cost a fortune in tokens?"**

It would — so the OS doesn't do that. `BOOT.md` is a small hot core (~4,500 tokens at v2.9.2) that carries a condensed rules digest and *pointers* to the full rules, skill procedures, and command catalog, rather than inlining them. Boot reads six small files — `BOOT.md`, `manifest.json`, `project_genome.json`, your active archetype file (on a fresh install, where the archetype is still `auto`, the archetype index first), a single-entry session-continuity summary, and the currently-open task memory file (`memory/tasks/*.md` — `BOOT.md` §2 step 4 requires one every session, including on `main`) — and stops there. The full text of `rules/*.md`, `registry/*/SKILL.md`, and `commands/index.json` (tens of KB combined) loads only when a specific situation actually calls for it: a rule conflict, a security-sensitive change, or a command being invoked.

Net effect: boot costs roughly **5,500–6,500 tokens** at v2.9.2 (characters ÷ 4; the task file's size is the one variable component), and that figure does not grow with the skills and full rule text, since those live in files that are opt-in by trigger, not opt-out by size. It does grow when `BOOT.md` itself grows, so the number is measured rather than remembered: `python .ai-os/scripts/context_footprint.py` prints the current figures for your project, and the framework's own development tests hold a ceiling on the always-loaded governance text. Provider-side prompt caching, which most hosted models offer, still helps on top of this for the parts that are read repeatedly, but it's a bonus, not the mechanism the design relies on.

**Exception — the Claude Code hook path.** That figure is the lazy-read path every host follows. On Claude Code the installed `SessionStart`/`SubagentStart` hook injects the full text of `BOOT.md` *and* `rules/ultimate_rules.md` unconditionally (about 31 KB combined at v2.9.2, so roughly **7,500–8,000 tokens** by the same characters-÷-4 estimate — a heuristic, not a tokenizer count), plus the task file. It does this again for **every dispatched subagent**, because subagents inherit none of the parent's context. That is the price of governance being present without relying on the agent to re-read it; if it matters more than that guarantee for your project, remove the `SubagentStart` entry from `.claude/settings.json`.

**Runtime cost control is a different layer.** Everything above is about what this framework itself adds to context. What a session spends *while working* — tool definitions re-sent on every request, turns stuck in a failure loop — is controlled at the host's hook level, which this framework does not implement. [TokenEconomizer](https://github.com/microsoft/TokenEconomizer) (Microsoft Research / UC Berkeley, Apache-2.0) does: it prunes tools a repository never uses and has a judged loop guard, and reports 18–31% lower mean cost on SWE-Bench tasks in its own paper. The two can be installed side by side. What follows was read from its source (commit `a345a9d`, 2026-11-15) and **has not been tested together with this framework**:
- On Claude Code its pruning never removes `Agent`, `Task`, `Skill`, `AskUserQuestion` or `ToolSearch`, so subagent review (`core.dev-loop.sk`) and the native skill pointers are not affected.
- On Codex it can switch off the `collaboration` capability package after enough sessions in which it went unused. That would drop the Review Pass to its same-agent fallback without saying so. Set `toolprune_protect=collaboration` in its config to prevent that.
- Both inject context at session start; the injections add up, they do not replace each other.

---

## System Structure

Kernel space (`BOOT.md`, `manifest.json`, `kernel/`, `rules/`, `genome/archetypes/`) is read-only for the agent unless your message contains the literal phrase `KERNEL OVERRIDE AUTHORIZED`; on Claude Code the host also asks you before such an edit. User space (skills, commands, memory) is where the framework changes itself, through proposals recorded in `progress.md`.

### What a session loads, and when

<img src="docs/context-loading.svg" alt="What a session loads. The host reads a bridge file, which points to BOOT.md. BOOT.md reads five small files every session, about 5,500 to 6,500 tokens. Four larger sources load only when triggered: the full rules on a rule conflict or security decision, a skill's SKILL.md and the command catalog when a command runs, and the first-boot wizard once ever. On Claude Code only, a SessionStart and SubagentStart hook also injects BOOT.md, ultimate_rules.md and the task file verbatim, about 8,000 tokens, at every session start and every subagent spawn." width="100%">

*The boot read stays the same size as skills and rules are added; only the hook path on Claude Code repeats its cost for every subagent.*

### How a note becomes project knowledge

<img src="docs/memory-promotion.svg" alt="How a note becomes project knowledge. Working notes go into the branch's task file unchecked. On TASK_CLOSE or MEMORY_CONSOLIDATE each candidate fact passes two gates: is it still true in the code now, and was the change it describes actually accepted, with owner sign-off on startup archetypes and above. A fact that fails either gate stays in the task file. A fact that passes both is written to knowledge/*.md, which every later session trusts without re-checking. An entry later found wrong goes through MEMORY_AMEND and the same gate." width="100%">

*Both gates exist because a true description of a change that was later reverted is still a bad thing to remember as "how it works".*

---

## Installation & Upgrade Guide

### Package Layout (Before Install)
The downloaded/cloned package lives anywhere on your machine — not inside your project.
```
maiks/
├── .ai-os/                          # The OS Kernel
├── .ai-os-installer/                # The Agentic Installer
│   ├── INSTALL_PROMPT.md            # The script you feed to your AI for first install
│   ├── UPDATE_PROMPT.md             # The script you feed to your AI for upgrading
│   └── templates/                   # Bridge file templates (CLAUDE.md, etc.)
└── README.md
```

### First-Time Installation
1. Download or clone MaiKS anywhere on your machine — it does **not** need to be inside your project. Leave it where it downloaded.
2. Open your project in your AI editor or launch your terminal assistant.
3. Open your AI chat and type: **"Please install the AI OS using the instructions in `<path-to-downloaded-package>/.ai-os-installer/INSTALL_PROMPT.md`"**
4. The agent acts as an installer: it copies just the `.ai-os/` folder into your project as its first step, merges the necessary bridge instructions into your existing rules (e.g., `.windsurfrules`, `CLAUDE.md`) without destroying them, and boots up. `.ai-os-installer/` is never copied in, so there's nothing to clean up afterward.
5. On first boot, the OS notices `manifest.json` is unpopulated and runs the **First-Boot Wizard** — it asks for your project name and runs a perception scan (`INFRA_DETECT_STACK`) to map your tech stack.

Once installed, your workspace looks like this:
```
your-project/
├── .ai-os/                          
│   ├── BOOT.md                      # Master boot prompt
│   ├── manifest.json                # Project config & metadata
│   ├── progress.md                  # Living dashboard & status tracker
│   ├── kernel/                      # System self-verification checks
│   ├── rules/                       # Governance rules, security & evolution policy
│   ├── commands/                    # User aliases and command catalog
│   ├── genome/                      # Detected stack DNA & Archetypes
│   ├── memory/                      
│   │   ├── episodic/                # decisions.jsonl, sessions.jsonl, last_session.json,
│   │   │                            # decisions.archive.jsonl (rotated on consolidation)
│   │   ├── semantic/                # project_knowledge.md (index) + knowledge/*.md + patterns.json
│   │   │                            # + generated/ (regenerable caches, e.g. dataflow_map.json)
│   │   ├── procedural/              # workflows.json + playbooks.md
│   │   ├── tasks/                   # Active Jira/feature branch working memory
│   │   ├── archived_tasks/          # History of closed tasks (pruned, not unbounded)
│   │   └── plans/                   # Dated approved plans (PLAN_WRITE / ARCHITECT_PLAN)
│   ├── agents/                      # Custom specialized agent profiles
│   ├── scripts/                     # task_identity.py, session hooks, context_footprint.py
│   └── registry/                    # Skill catalogs (.sk/), incl. core.memory.sk
│
├── .gitignore                       # (Updated by installer to ignore OS noise)
├── src/                             # (Your actual app code)
│
├── AGENTS.md                        # Root bridge — universal fallback, always added
└── [Host-Specific Bridge File]      # (Merged by the installer)
    ├── CLAUDE.md                    # ...if using Claude Code, plus .claude/settings.json
    │                                #    (hooks, kernel-edit prompts) and .claude/skills/ai-os-*/
    ├── .windsurfrules               # ...if using Windsurf
    ├── .cursor/rules/ai-os.mdc      # ...if using Cursor (alwaysApply: true frontmatter)
    ├── .github/copilot-instructions.md # ...if using GitHub Copilot
    └── .agents/AGENTS.md            # ...if using Antigravity/Gemini
```

### Upgrading
**WARNING**: Do **not** overwrite your existing `.ai-os/` folder manually — doing so will wipe out your AI's memory.

1. Download the new version of MaiKS anywhere on your machine, as for a first install.
2. Open your AI chat and type: **"Please update my AI OS using the instructions in `<path-to-new-package>/.ai-os-installer/UPDATE_PROMPT.md`"**
3. The agent acts as a safe updater: it copies the new kernel, rules, and skills, while guarding your `memory/` folder so it isn't overwritten, and merges any new settings into your `manifest.json`.

---

## Efficient Workflow

How to get the most out of MaiKS in your daily development:

1. **The Boot**: While the bridge files naturally instruct the agent to read `.ai-os/BOOT.md` in the background, LLMs don't always act until spoken to. Begin your first chat of the day with: **`> OS_COMMAND BOOT`** to ensure a verified load of your project's memory.
2. **Branch Auto-Detection (Zero Setup)**: Start a new ticket by checking out a branch (e.g., `git checkout -b feature/JIRA-123`). The OS will automatically detect this branch and create a dedicated, isolated task memory file in `.ai-os/memory/tasks/`, named from a readable slug plus a SHA-256 of the exact branch name (`task-feature_JIRA-123-81ef6e….md`), so `feature/a_b` and `feature_a/b` never share one. It will use this file to log deep technical debugging steps so your main project memory isn't polluted — and it'll do the same even if you work directly on `main`/`release` (solo projects, hotfixes, trunk-based workflows). There's no branch where working notes are allowed to skip straight to permanent project memory unverified; on those protected branches the task file is just *rolling* — periodically drained into `project_knowledge.md` by `MEMORY_CONSOLIDATE` instead of closed all at once by `TASK_CLOSE`. Not in a git repo, or in a detached `HEAD` state with no branch to key off? The OS won't skip task memory or invent a name for you — it checks for an already-open task first, and if it can't find one, it just asks what you're working on before creating the file.
3. **Daily Development**: Code normally! You don't need to micromanage the OS. Just ask your agent to build features, fix bugs, or write tests. The OS's security and design rules govern it silently as it works.
4. **Complex Planning**: If you have a big structural change, don't just tell the agent to code. Which command depends on where you're starting from — the two don't overlap. Starting a whole new idea with no project yet? Type `> OS_COMMAND plan`; the `Architect` skill runs a structured interview through project scaffolding. Already inside this project and planning a feature or fix? Type `> OS_COMMAND feature` (`PLAN_BRAINSTORM`) instead; it clarifies scope through a few rounds of questions, writes a concrete step-by-step plan, then executes it with verification at each step.
5. **Task Completion & Consolidation**: When you finish your feature and are ready to open a Pull Request, tell the agent: **`> OS_COMMAND TASK_CLOSE`** (or just say "summarize and close this task"). The AI reads your task memory, checks each candidate fact two ways — is it still factually accurate, and was the underlying change actually accepted rather than still buggy or awaiting your sign-off — before saving anything to the `semantic/` hub, then archives the task file. Nothing gets promoted to permanent memory just because it was written down.

---

## Backup & Restore (Portability)

MaiKS stores all of its memory, skills, and governance as plain-text Markdown and JSON files within your workspace, so this state travels with your code.

- **To Backup**: Commit the `.ai-os/` directory to your project's Git repository.
- **Merge Conflicts?**:
  - *Append-only Logs (`decisions.jsonl`)*: two branches that both append to it conflict at the end of the file. Every line is a self-contained JSON entry, so the fix is to keep both sides' lines. Adding `.ai-os/memory/episodic/decisions.jsonl merge=union` to your `.gitattributes` makes Git do that automatically.
  - *Semantic Memory (`knowledge/*.md`, indexed by `project_knowledge.md`)*: institutional knowledge is split into topic files to keep concurrent branches from touching the same file. Before deleting something as superseded, it checks Git history first — if another branch added that entry after your branch forked, it flags the conflict instead of silently dropping it on merge. A conflict reaching you is a signal something needs a human look, not intended behavior.
  - *Noisy Files*: The installer adds per-machine files (`sessions.jsonl`, `last_session.json`, `session_override.json`, and `progress.md`) to your `.gitignore` to reduce merge conflicts — `decisions.jsonl` itself stays tracked, since it's the shared audit trail.
- **To Restore**: When you clone your repo on a new machine (or a teammate clones it), the host AI agent reads the same episodic memories, structural rules, and custom skills. No external database to sync.

---

## Command Reference

MaiKS commands can be invoked with **natural language** — you don't need exact command syntax; the AI matches your request to the closest command. The tables below list the commands you'll use most; `HELP` or `.ai-os/commands/index.json` has all of them. Every command — built-in or skill-owned — runs through the same invocation pipeline:

<img src="docs/command-invocation-flow.svg" alt="Command invocation flow. A command arrives typed as OS_COMMAND, through an alias, or as a plain-English request matched to the closest command; all three resolve against commands/index.json. A built-in runs its procedure from BOOT.md; any other command loads its registry SKILL.md. Both print the one-line AI-OS banner, then run the procedure, optionally calling a reviewer subagent or a chained command. The result is verified: on pass a significant decision is logged and memory is written through its gate; on fail the result is reported as not verified, and an evolution is rolled back. Both end in a report to the user." width="100%">

*Blue = built-in · amber = skill command (loads a `registry/*/SKILL.md`) · green = verified · red = not verified · dashed = optional, not every command takes it.*

### Core System
| Command | Alias | Description | Example Prompt |
|---|---|---|---|
| `STATUS` | `status` | Show system health and memory stats | *"Can you check the OS status?"* |
| `HELP` | | List every available command | *"What commands can you run?"* |

### Security & Healing
| Command | Alias | Description | Example Prompt |
|---|---|---|---|
| `SECURITY_AUDIT` | `audit` | Full workspace security review | *"Please audit the workspace before we commit"* |
| `SECURITY_SCAN_FILE` | `scan` | Security review on a specific file | *"Check auth.ts for security flaws"* |
| `HEAL_DIAGNOSE` | `fix` | Run troubleshooting checklist | *"I'm stuck in an error loop, please run a diagnosis"* |
| `HEAL_REPAIR` | `repair` | Execute an auto-repair sequence | *"Go ahead and repair that issue"* |
| `REVIEW_CREDIBILITY` | | Audit docs/claims for overclaims and stale info | *"Review this README for anything that's gone stale"* |

### Planning & Infrastructure
| Command | Alias | Description | Example Prompt |
|---|---|---|---|
| `ARCHITECT_PLAN` | `plan` | Greenfield only: interview an idea into an architecture plan and scaffold | *"I have an idea for a recipe app and nothing is built yet"* |
| `PLAN_BRAINSTORM` | `feature` | Clarify a feature or change inside this project before planning it | *"Let's plan a new user dashboard feature"* |
| `PLAN_WRITE` | | Write a step-by-step plan to `memory/plans/` | *"Write up the plan for the export feature"* |
| `PLAN_EXECUTE` | | Work an approved plan, with a review pass at the end | *"Execute the approved plan"* |
| `DEV_IMPLEMENT_REVIEWED` | | Implement a small task without a plan, then an independent review | *"Add a /health endpoint"* |
| `SIMPLIFY_REVIEW` | `simplify` | Review a diff for over-engineering only | *"Is this diff more complex than it needs to be?"* |
| `INFRA_DISCOVER_MODULES` | `discover` | Profile codebase to detect stack drift | *"Profile the codebase, I just added Next.js"* |
| `INFRA_SCAFFOLD` | | Generate boilerplate project structure | *"Scaffold the project structure for me"* |
| `INFRA_ANALYZE_COMMITS` | `absorb_history` | Seed semantic memory from recent PR-merge history | *"Absorb our commit history into project memory"* |
| `INFRA_MAP_DATAFLOW` | `trace` | Trace a field to every place it's read/stored/emitted, or trace a sink back to its inputs | *"Where does the signup email field end up?"* |

### Memory & Evolution
| Command | Alias | Description | Example Prompt |
|---|---|---|---|
| `WRAP` | `wrap` | Pause the session — save continuity, promote nothing | *"Let's stop here for today"* |
| `TASK_CLOSE` | `close` | Execute the Consolidation Protocol | *"I'm done with this branch, summarize and close the task"* |
| `MEMORY_CONSOLIDATE`| `consolidate`| Extract rules into semantic memory | *"Extract the rules we just learned into memory"* |
| `MEMORY_AMEND` | `amend` | Correct or retract a semantic-memory entry that turned out wrong | *"That convention in the docs is actually what caused this bug"* |
| `EVOLVE_PROPOSE` | `propose` | Draft a PDCA system upgrade | *"Propose a new command to automate docker builds"* |
| `EVOLVE_APPLY` | `apply` | Apply an approved evolution | *"That proposal looks good, apply it"* |

### Testing
| Command | Alias | Description | Example Prompt |
|---|---|---|---|
| `TEST_RUN` | `test` | Execute the test suite | *"Run the tests"* |
| `TEST_GENERATE` | | AI-assisted test generation | *"Write some robust tests for this new utility"* |

---

*MaiKS v2.9.2*
