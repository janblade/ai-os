# 🔄 AI OS Agentic Updater

**ATTENTION AI AGENT**: You are currently acting as the MaiKS System Updater. The user has downloaded a new version of the OS framework. Your job is to upgrade their existing `.ai-os` installation **without destroying their memory**.

## ⚡ Execute Independent Steps in Parallel
Wherever a step below lists multiple file operations that don't depend on each other's
output (different target files, no ordering requirement), issue them as parallel/batched
tool calls instead of one round-trip per file — this is the main lever for a fast update.
Serialize only where a step explicitly says one action must precede another (e.g. a
directory must exist before files are moved into it, or a migration assumes an earlier
one already ran).

## Step 1: Identify the Source
Ask the user for the path to the newly downloaded MaiKS update folder (e.g., `./maiks-update`). Wait for their confirmation before proceeding. Before touching anything, read the user's *current* `.ai-os/manifest.json.ai_os_version` and hold onto it — Step 4 needs it to know which migrations actually apply.

## Step 2: The Memory Guard & Layout Migration (CRITICAL)
You **MUST NOT** overwrite, delete, or lose the user's existing memory file contents (such as `project_knowledge.md`, `decisions.jsonl`, `sessions.jsonl`, and custom task logs). However, you **MUST** ensure the memory layout is migrated to the new four-tier directory structure. Sub-steps 1 and 2 are each a batch of independent filesystem operations (different directories/files, no ordering between entries within a sub-step) — do each sub-step's items in one parallel pass, not one directory or file at a time; only sub-step 2's moves must wait on sub-step 1's directories existing.
1. Ensure all new memory subdirectories exist in the user's active `.ai-os/memory/`:
   - `semantic/`
   - `semantic/knowledge/`
   - `semantic/generated/` (regenerable caches, e.g. `INFRA_MAP_DATAFLOW`'s dataflow map —
     self-creates on first write either way, but ensure it exists for consistency)
   - `episodic/`
   - `procedural/`
   - `tasks/`
   - `archived_tasks/`
   - `plans/` (dated plan files from `PLAN_WRITE`/`ARCHITECT_PLAN`, v2.7.0 cont'd 3 —
     ensure it exists with a `.keep`; never delete or overwrite plan files already in it)
2. Safely migrate existing files from old locations (e.g. root of `.ai-os/memory/`) to their new subdirectories if they are found in the old location:
   - Move `project_knowledge.md` and `patterns.json` to `.ai-os/memory/semantic/`
   - Move `decisions.jsonl` and `sessions.jsonl` to `.ai-os/memory/episodic/`
   - Move `workflows.json` and `playbooks.md` to `.ai-os/memory/procedural/`
   - Move any task files (e.g., `JIRA-*.md`) to `.ai-os/memory/tasks/`
3. **Indexed Semantic Knowledge Segregation**:
   If the user has a monolithic `project_knowledge.md` (without a `.ai-os/memory/semantic/knowledge/` directory):
   - Create `.ai-os/memory/semantic/knowledge/`.
   - Read the user's existing `project_knowledge.md` and parse its sections.
   - Write their section contents into specialized files under `knowledge/` (e.g., `architecture_overview.md`, `conventions_patterns.md`, `known_gotchas.md`, or custom category files based on their headers).
   - Rewrite their `.ai-os/memory/semantic/project_knowledge.md` as an index document linking to those sub-files so all their existing knowledge is preserved and properly segregated.
4. Copy any default templates or placeholder files (like `.keep` files, default `patterns.json`, etc.) from the update source's `memory/` folder ONLY if the user does not already have an existing version of that file. If this is copying `playbooks.md` or `workflows.json` in specifically because the user's install is missing it, strip any project-only content from the copy first, same as `INSTALL_PROMPT.md` Step 4 item 10 (EP-75): drop any `## Playbook:` section marked `**Project-only**`, and any `workflows.json` entry with `"project_only": true`. Every other install already has its own copy and is untouched by this step regardless.
5. If missing, create `.ai-os/memory/episodic/last_session.json` (seed it from the last entry in the user's existing `sessions.jsonl`, or a null placeholder if empty).

## Step 3: Perform the Upgrade

**Step 3a — Project-Specific Addendum (always, unconditionally, before touching `rules/`).**
`rules/ultimate_rules.md` has a structurally-marked section for the user's own rules:
`<!-- PROJECT_RULES_START -->` ... `<!-- PROJECT_RULES_END -->`. This survives on its own
marker, not on whether a decision-log entry happens to exist — don't gate its preservation
on the log search in Step 3b. Extract whatever's between those markers in the user's
current file (empty is fine, nothing to preserve). After copying in the new
`ultimate_rules.md`, re-insert that content between the new version's own markers before
anything else touches the file. If it's written in full prose rather than the compact
style `rules/evolution_policy.md`'s Authoring Style section specifies (v2.5.0+), offer to
compact it, showing a before/after example first — never rewrite it without that
confirmation, no matter how verbose it looks.

**Step 3b — everything else in `BOOT.md`, `kernel/`, or `rules/` — check for authorized
kernel customizations.** These are kernel space: the framework's own rule (`BOOT.md`
"BOUNDED AUTONOMY") says an agent may never edit them without the user's literal phrase
`KERNEL OVERRIDE AUTHORIZED`, and every such edit is supposed to be logged. Unlike the
Addendum, a modification to *existing* rule text or `BOOT.md` content carries no in-file
marker distinguishing it from stock content — a blind diff can't tell "stock content the
new version restructured away" from "a customization about to be silently destroyed," so
log search is the only signal available here (imperfect: it depends on logging having
actually used a recognizable phrase — treat a miss as "nothing detected," not "confirmed
nothing to preserve").
1. Search `decisions.jsonl` (and `decisions.archive.jsonl` if it exists, and `progress.md`'s
   Evolution Proposal history) for any entry mentioning `KERNEL OVERRIDE` that targets
   `BOOT.md`, a `kernel/*` file, or a `rules/*` file.
2. None found → overwrite these freely with the update source's versions (Addendum content
   from 3a still gets re-inserted regardless).
3. Found → read the specific section each entry describes in the user's current file, check
   whether an equivalent exists in the new source's version. Missing or would be overwritten
   → tell the user exactly what's about to be lost (quoting the original decision log
   entry), ask whether to re-apply it on top of the new version — the same intelligent-merge
   approach `INSTALL_PROMPT.md` already uses for bridge files, not a mechanical patch — skip
   it, or proceed with the loss deliberately. Never silently overwrite once a relevant log
   entry is found. Same compaction offer as 3a if it's written in prose.

Then copy the remaining files and directories from the new update source into the user's
active `.ai-os/` directory, overwriting the old versions. **This list is exhaustive on both
sides — copy everything named under "Copy", touch nothing named under "Never copy."** A
directory absent from both lists is a bug in this file, not a licence to guess: name it to
the user and ask.

Split this by what each entry actually needs: `scripts/`, `genome/archetypes/`,
`agents/supervisor.json`, `agents/templates/`, and (once the kernel-space check above has
cleared them) `BOOT.md`/`kernel/`/`rules/` carry no per-file judgment — do these as bulk
filesystem copies (e.g. one recursive directory copy per entry) rather than reading and
rewriting file-by-file. Only `registry/index.json`, `commands/index.json`,
`commands/aliases.json`, `agents/index.json`, and `manifest.json` (see the Note below) need
the old-vs-new read-and-merge treatment — read all of their old/new pairs in parallel up
front rather than one pair at a time, then apply each merge.

**Copy:**
- `BOOT.md`, `kernel/`, `rules/` (per the check above)
- `registry/` (Merge `index.json` carefully to preserve custom skills! This also brings in any new core skills the user doesn't have yet — diff the update source's `registry/index.json` skill IDs against the user's, and copy in any folder that's new.)
- `commands/`
- `scripts/` — framework-owned tooling, no user content, straight overwrite. **Do not skip
  this.** Step 5's hook check assumes the current `session-start-hook.sh` is on disk; leaving
  a stale copy while adding the new `SubagentStart` settings entry produces a hook that fires
  on a subagent event and reports `hookEventName: "SessionStart"` — the injection is wrong or
  silently dropped, which is the exact failure that entry exists to prevent (v2.7.0/EP-60
  gave the script an optional first argument; older copies ignore it).
- `genome/archetypes/` only — the pre-defined governance profiles, framework-owned.
- `agents/supervisor.json` and `agents/templates/` — framework-owned. Merge
  `agents/index.json` the same way as `registry/index.json`: it carries user-defined external
  agents auto-registered by Local Agent Absorption, so preserve their `active_profiles`
  entries and add only genuinely new framework ones.

**Never copy** (project-owned — overwriting these destroys the user's work):
- `memory/` — Step 2 owns this entirely.
- `genome/project_genome.json` — the user's own detected genome.
- `progress.md` — the user's own evolution history.
- `manifest.json` — merge-only, per the note below.

*Note: For `manifest.json`, `registry/index.json`, `commands/index.json`, and `commands/aliases.json`, do not blindly overwrite. Read both the old and new versions, and carefully merge any new configuration keys, framework skills, or new core commands/aliases from the update into the user's existing files to preserve their custom settings, custom skills, and custom aliases. Confirm any new skill IDs present in the update's `registry/index.json` are also added to the user's `manifest.json.installed_skills` array — a skill folder copied to disk but missing from that list won't be treated as installed. Once everything else is merged, set `manifest.json.ai_os_version` to the update source's version — this is the one field that's supposed to change wholesale, not merge.*

*Exception: `EVOLVE_BENCHMARK`, `RELEASE`, and `PUBLISH` are project-only commands specific to MaiKS's own dev repo (see `INSTALL_PROMPT.md` Step 4 items 8, 9, and 11) — never add their `commands/index.json` entries, their strings in `registry/index.json`'s `core.evolution.sk.commands` array, or `RELEASE`'s `"release"`/`"ship"` or `PUBLISH`'s `"publish"` keys in `commands/aliases.json` during this merge, even though the update source's copy has all of them. If the user's own `.ai-os/` already has any of these (e.g. from before this exclusion existed), leave it as their own customization — don't strip it retroactively.*

## Step 4: Execute Migrations
`.ai-os-installer/MIGRATIONS.md` is a reverse-chronological list of version sections and can
grow large — don't read it in full by default. First grep its `## ` headers (cheap) to find
the pre-upgrade `ai_os_version` you captured in Step 1; since sections run newest-to-oldest,
every applicable section (newer-than-or-equal-to, see below) is one contiguous block from the
top of the file down through — and including — that version's own section. Read only that
span in full. Fall back to reading the whole file only if the old version's header can't be
found (e.g. a version string that predates this file, or the fresh-from-`v1.0.0` case) —
never guess the boundary. Using the pre-upgrade `ai_os_version` you captured in Step 1:
1. Walk every version section **newer than or equal to** the user's old version,
   oldest-of-those-first (i.e. if upgrading from v1.0.0 to v2.1.1, apply v2.0.0's actions,
   then v2.1.0's, then v2.1.1's, in that order — later migrations can assume earlier ones
   already ran).
   **Why "or equal to" and not just "newer":** a release can add content under a version
   number that already shipped — the `v2.7.0 (cont'd)` and `v2.7.0 (cont'd 2)` sections are
   exactly that, additive skill/script changes that by precedent don't bump `ai_os_version`.
   A strict "newer than" walk skips them for every user already on that version, which is
   precisely the population they were written for. Re-running the current version's section
   is the cost of catching those, and it is safe because of the rule in step 2.
2. For each: review deprecations/obsoleted files and delete ONLY files explicitly listed as
   obsolete (never other files in the user's `registry/` or `commands/` — those may be
   custom). Then perform whatever action that version's entry describes (e.g. an orphan
   sweep, a schema note, a file that needs seeding) — treat every `Migration action:` line
   in each section as a step to actually execute, not background reading.
   **Every migration action is idempotent and must stay that way** — written as "ensure X
   exists," "merge Y if missing," "move Z if still in the old location," never as a blind
   append or an unconditional overwrite of user content. Step 1 re-runs the current
   version's section on every update, so a non-idempotent action would corrupt a little more
   each time. Writing a new section? Satisfy this or the section is wrong.
   Sections still get walked oldest-of-the-applicable-first, but actions that target
   different files with no dependency between them (within one section, or across sections
   once read) can be batched as parallel tool calls — only serialize an action that depends
   on an earlier one's output (e.g. a file a prior section's action just created or moved).
   An action whose idempotent check already passes needs no write, just the check.
3. The user already being on the latest version does **not** make this a no-op — their
   version's own section still gets walked, per step 1. Nothing to do only when that
   section's actions are all already satisfied; confirm that explicitly rather than
   skipping the check on the version number alone.

This replaces having a separate hardcoded step per version (e.g. an old "v2.1.0-only" step)
— new versions just add a new MIGRATIONS.md section and this loop picks them up
automatically, so this file doesn't need editing every release.

## Step 5: Verify and Finalize
1. Verify that the migrated memory files (specifically `.ai-os/memory/semantic/project_knowledge.md` and `.ai-os/memory/episodic/decisions.jsonl`) are intact.
2. Refresh the user's `.gitignore` "AI OS Ephemeral Memory" block against the current list in `INSTALL_PROMPT.md` Step 5 — if they installed under an older installer version, they may be missing a newer ephemeral file (e.g. `last_session.json`).
3. If this is a Claude Code host (a root `CLAUDE.md` exists, or `.claude/` does), refresh
   `.claude/settings.json` against `.ai-os-installer/templates/claude-code-hooks.json` the same
   way as the gitignore check above — if `hooks.SessionStart` is missing the current
   `startup|clear|compact`-matcher entry, **or `hooks.SubagentStart` is missing entirely**,
   merge the missing entry in without touching any other hooks the user has configured. This
   also covers upgrading an older install that only has the earlier `compact`-only
   echo-reminder version of this hook — replace that entry with the current one rather than
   leaving both, since `.ai-os/scripts/session-start-hook.sh` (the script both entries call)
   lands automatically as part of the normal `.ai-os/` payload copy. This check is
   unconditional and re-runs every update, not gated by version — it doesn't rely on
   `MIGRATIONS.md`'s walk.
   - The `SubagentStart` entry is new in v2.7.0 (EP-60), so every pre-existing install is
     missing it. It passes the event name as the script's first argument; the script defaults
     to `SessionStart` when called with none, so an existing `SessionStart` entry keeps working
     unchanged and must not be rewritten.
   - If the user already narrowed their own `SubagentStart` matcher (it filters on agent type),
     leave their value alone — do not widen it back to `.*`. See `INSTALL_PROMPT.md` Step 3 for
     the token cost that motivates narrowing it.
4. Do NOT delete the update source folder. Leave it intact so the user can reference it if needed.
5. Announce to the user that the upgrade is complete, stating the old and new `ai_os_version`.
