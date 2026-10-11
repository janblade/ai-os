# 🔄 AI OS Migrations & Deprecations

This file tracks feature, file, and skill changes — additions, deprecations, and removals —
across MaiKS versions, in reverse-chronological order.
The Agentic Updater (`UPDATE_PROMPT.md`) reads this file during upgrades to safely prune obsolete framework files without destroying the user's custom skills.

**Rule for anyone writing a new section:** every `Migration action:` must be idempotent —
"ensure X exists," "merge Y if missing," "move Z if still in the old location," never a blind
append or an unconditional overwrite of user content. `UPDATE_PROMPT.md` Step 4 walks every
section **newer than or equal to** the user's current version, so the current version's
section re-runs on every update. That walk is what lets a `(cont'd)` section — additive
content shipped under a version number that already exists, which by precedent doesn't bump
`ai_os_version` — actually reach the users already on that version. A non-idempotent action
would corrupt a little more on each pass.

## v2.9.0 — Reproducible Context and Executable Memory Gates

- **Context runtime:** Python 3.10+, no third-party dependencies. Stable task IDs,
  selected source hashes/reasons, UTF-8 rendering, private snapshots, replay, and
  diffs. PACT-inspired, without a browser DOM or full PACT conformance claim.
- **Memory gates:** identified entries, checks against explicit dependencies,
  fresh evidence, reviewed task/destination hashes, selective draining, amendment,
  cooperative locking, and recovery journals. Unresolved/unselected notes and
  active plan pointers survive promotion. Acceptance flags do not prove human approval.
- **Host hooks:** shared startup/subagent context, mutation checks, changed-item
  updates, and completion checks. Claude Code 2.1.295+ supports fail-closed gates;
  Codex explicit denials work on supported tools but launch failures can fail open.
  Native host permissions and Codex hook trust remain required.
- **Authority:** host/user instructions outrank framework defaults. Existing scoped
  user authorization persists; model-written override files never grant permission.
- **Migration action:** ensure new scripts exist, then run `install-hooks` with
  the relevant package template. Preserve unrelated settings and narrowed subagent
  matchers; review/trust changed Codex hooks in `/hooks`. Keep `memory/runtime/`
  ignored and private; never copy runtime state into another project. Retain legacy
  task files, add an exact original `Branch:` header only after ownership review,
  and resolve names through the CLI. Never bulk-rename or clear existing notes.
  Existing installs lacking bridges skip fresh-install resets. Re-running hook
  installation or checking a migrated knowledge index is idempotent.
- Measurement and limitations: `docs/context-runtime.md` and
  `docs/context-measurement.json` in the source package.

## v2.8.0 — Automatic Peer Review on Plan Execution

- **`PLAN_EXECUTE` now runs a review pass automatically** (EP-67): `core.planning.sk` gained
  `core.dev-loop.sk` as a dependency and invokes its new **Review Pass** sub-procedure once
  per flat plan (at completion, on the accumulated diff) and once per epic story (at the
  story-done gate, on that story's diff). The pass is an independent reviewer subagent where
  the host supports subagent dispatch, an honestly-labeled cold self-review where it
  doesn't; findings surface to the user, non-blocking. **Migration action:** none —
  additive skill content, covered by the `registry/` copy in `UPDATE_PROMPT.md` Step 3.
  Existing plan files are unaffected.
- **`core.dev-loop.sk` refactor** (EP-67): the review half of `DEV_IMPLEMENT_REVIEWED` is
  factored into a named `### Review Pass` section that both `DEV_IMPLEMENT_REVIEWED` and
  `PLAN_EXECUTE` call. `DEV_IMPLEMENT_REVIEWED` behavior is unchanged. No migration action —
  skill-file content, covered by the Step 3 copy.
- **New `BOOT.md` §4 routing rule** (EP-67): a plain-English "implement this feature /
  endpoint / function" request **with no approved `PLAN_WRITE` plan** now routes to
  `DEV_IMPLEMENT_REVIEWED` instead of a bare in-thread write. Granular edits (fix a line,
  rename a symbol) still match nothing; "execute the plan" when a plan exists still routes
  to `PLAN_EXECUTE`. No migration action — `BOOT.md` content, covered by the Step 3 copy
  (itself gated by this repo's `KERNEL OVERRIDE`).
- **Cost note for upgraders:** on a host with subagent dispatch this adds roughly one
  reviewer subagent (~6.5K tokens, per the v2.7.0(cont'd 2) `SubagentStart` measurement)
  per plan, per epic story, and per plan-less implement. On a host without it, the pass is a
  cold re-read — no dispatch, negligible cost. There is deliberately no archetype gate and
  no `--no-review` opt-out in this release; if the cost is unwanted, the narrowest local
  change is to add a `--no-review` parameter to `PLAN_EXECUTE`.
- **`ai_os_version` bumped `2.7.0` → `2.8.0`** — unlike the additive `(cont'd)` releases,
  this one changes *default execution behavior* with a real per-run token cost, which an
  upgrading project should consciously notice. `UPDATE_PROMPT.md` Step 4 walks this section
  on any install below 2.8.0.

## v2.8.0 (cont'd) — Ownership-Fit Lens in the Review Pass

- **`core.dev-loop.sk`'s Review Pass gained a fifth check** (EP-68): alongside correctness,
  convention adherence, security, and test coverage, both branches (independent reviewer
  subagent / cold self-review) now check **ownership fit** — "if you owned this repo, would
  you merge this diff as-is, or is it in the wrong module / at the wrong abstraction /
  under-designed even though it works?" Distinct from `core.simplicity.sk`, which is scoped
  to over-engineering only. Findings surface to the user, non-blocking, same as the other
  four. Because `PLAN_EXECUTE` and `DEV_IMPLEMENT_REVIEWED` both call the one Review Pass
  sub-procedure, the lens reaches every implementation the pass already runs on — no new
  invocation, no added per-run cost. **Migration action:** none — additive skill-file
  content, covered by the `registry/` copy in `UPDATE_PROMPT.md` Step 3.
- **No `ai_os_version` bump** — additive content, consistent with the v2.1.0/EP-43
  precedent. EP-67 bumped `2.8.0` because it added a per-run token cost; this EP adds a
  criterion to a pass that already runs, so no bump. `UPDATE_PROMPT.md` Step 4 walks this
  `(cont'd)` section on any install at or below 2.8.0.

## v2.8.0 (cont'd 2) — Simplicity Ladder Wired Into PLAN_EXECUTE

- **`PLAN_EXECUTE` now applies the Simplicity Ladder before writing each step's code**
  (EP-70): `core.planning.sk` gained `core.simplicity.sk` as a dependency. Step 2 now stops
  at the first rung that holds (YAGNI → reuse → stdlib → native platform → existing
  dependency → one line → minimum code) before implementing a step, at the project's
  archetype-derived intensity from `core.simplicity.sk`'s own Intensity table — no new flag,
  no change to that table. Previously the ladder only ran when `SIMPLIFY_REVIEW`/
  `SIMPLIFY_AUDIT` was invoked by name, post-hoc on a diff that already existed; planned
  work had no caller for it despite the skill describing itself as a "pre-mutation ladder."
  **Migration action:** none — additive skill-file content, covered by the `registry/` copy
  in `UPDATE_PROMPT.md` Step 3.
- **No `ai_os_version` bump** — no new dispatch, no measurable per-run cost (unlike EP-67's
  Review Pass subagent): this cites an existing in-thread discipline at a step boundary that
  already runs one, the same way `PLAN_WRITE`/`PLAN_EXECUTE` already cite `core.testing.sk`'s
  TDD discipline without a version bump. `UPDATE_PROMPT.md` Step 4 walks this `(cont'd)`
  section on any install at or below 2.8.0.

## v2.8.0 (cont'd 3) — playbooks.md Actually Gets Read

- **`HEAL_DIAGNOSE` and the Repair Protocol now check `memory/procedural/playbooks.md`
  before diagnosing** (EP-72): previously the file was write-only — the Repair Protocol
  offered to save a hard-won fix "so I know how to resolve it automatically next time," but
  nothing ever consulted it again, on any path. `HEAL_DIAGNOSE` step 1 and the Repair
  Protocol's own step 1 (it also fires ambiently on loop detection, not only via an
  explicit `HEAL_DIAGNOSE` call) now scan playbook titles/`### When to Use` lines for a
  match before running a fresh diagnosis or looping into a new hypothesis. **Migration
  action:** none — additive skill-file content, covered by the `registry/` copy in
  `UPDATE_PROMPT.md` Step 3. Existing `playbooks.md` content is unaffected; the file's
  existing 6 template playbooks already have the `## Playbook:` / `### When to Use` /
  `### Steps` shape the new read step expects.
- **Repair Protocol's write step tightened**: a new playbook entry must follow that same
  three-part shape (not free-form notes) so the new read step can actually match against
  it — previously unspecified.
- **No `ai_os_version` bump** — additive, no new dispatch, same reasoning as EP-70/68: an
  in-thread text-file read, not a subagent cost. `UPDATE_PROMPT.md` Step 4 walks this
  `(cont'd)` section on any install at or below 2.8.0.

## v2.8.0 (cont'd 4) — workflows.json Gets a Real Reader and Writer

- **`PLAN_WRITE`/`PLAN_EXECUTE` now actually use `memory/procedural/workflows.json`**
  (EP-74): the file was referenced as a read source (`CONTEXT_LOAD` step 5, `BOOT.md` §8)
  and a nominal `EVOLVE_APPLY` write target for `workflow_optimization` proposals, but
  nothing had ever written to it — it shipped permanently empty (`"workflows": []`).
  `PLAN_WRITE` gains a new step 1: check `workflows.json` for an entry whose `trigger`
  matches the request, offering it as a starting point instead of drafting from scratch.
  `PLAN_EXECUTE` gains a new step 7: on completion, if the plan's step sequence is a
  genuinely repeatable pattern (judgment call, not automatic — most plans are one-off),
  offer to save it as a new entry matching the file's existing schema. Reusing a matched
  entry bumps its `success_count`/`last_used`. **Migration action:** none — additive
  skill-file content, covered by the `registry/` copy in `UPDATE_PROMPT.md` Step 3. The
  user's own `workflows.json` content (if any) is untouched — memory files are
  project-owned and `UPDATE_PROMPT.md` Step 2 item 4 only copies the default template
  when the user doesn't already have one.
- **`PLAN_WRITE`'s existing steps renumbered** 1–6 → 2–7 to make room for the new step 1;
  every in-file cross-reference to a `PLAN_WRITE` step number updated to match.
- **No `ai_os_version` bump** — additive, no new dispatch, same reasoning as EP-68/70/72:
  a text-file read/append, not a subagent cost. `UPDATE_PROMPT.md` Step 4 walks this
  `(cont'd)` section on any install at or below 2.8.0.

## v2.8.0 (cont'd 5) — Project-Only Playbooks/Workflows Excluded From Installs

- **New marker convention for repo-specific procedural memory** (EP-75): a `playbooks.md`
  playbook or `workflows.json` workflow that documents MaiKS's own dev process (not meant
  for any project that installs the framework) is now markable the same way `RELEASE`/
  `EVOLVE_BENCHMARK` already are as commands — `**Project-only**` directly under a
  `## Playbook:` heading, or `"project_only": true` on a `workflows.json` entry.
  `INSTALL_PROMPT.md` Step 4 gained item 10, stripping both on fresh install.
  `UPDATE_PROMPT.md` Step 2 item 4 gained the same strip for the one edge case where it
  applies there too — copying a default `playbooks.md`/`workflows.json` in because an
  existing install is missing the file entirely (every install that already has its own
  copy is untouched by that step regardless, so this only closes the missing-file gap).
  **Migration action:** none — additive convention, no existing playbook/workflow entry
  is retroactively marked; covered by the `registry/`-adjacent `memory/procedural/` and
  installer-doc copies already in `UPDATE_PROMPT.md` Step 3 / this file's own propagation.
- **No `ai_os_version` bump** — additive convention with no entries yet using it in this
  release; no new dispatch. `UPDATE_PROMPT.md` Step 4 walks this `(cont'd)` section on any
  install at or below 2.8.0.

## v2.8.0 (cont'd 6) — PUBLISH Splits the Repo Into Private/Public Halves

- **New `PUBLISH` project-only command** (EP-76): MaiKS's own single public GitHub repo
  exposed its full internal dev history (`progress.md`, `decisions.jsonl`, project-only
  commands) to anyone browsing or cloning it directly — `INSTALL_PROMPT.md` Step 4 only
  ever cleaned a *copy* made into a new project, never the source repo itself. Fix: the
  repo splits into a private dev repo (unchanged development, all history intact) and a
  separate public `ai-os` distribution repo containing only the stripped payload.
  `PUBLISH`, registered exactly like `RELEASE`/`EVOLVE_BENCHMARK` (same 4 registration
  points, same Addendum documentation), ships the current `.ai-os/`/`.ai-os-installer/`
  to that public repo by applying `INSTALL_PROMPT.md` Step 4's existing strip rules
  (items 1–11, `PUBLISH` itself now included) to a fresh scratch clone rather than
  duplicating them. **Migration action:** none — additive command content, covered by the
  `registry/`/`commands/` merge in `UPDATE_PROMPT.md` Step 3 (with `PUBLISH` added to the
  same never-merge exception list `RELEASE`/`EVOLVE_BENCHMARK` already have).
- **No `ai_os_version` bump** — additive command content, consistent with the
  `RELEASE`/EP-66 precedent (a project-only command's own addition never bumped the
  version either). `UPDATE_PROMPT.md` Step 4 walks this `(cont'd)` section on any install
  at or below 2.8.0.

## v2.7.0 (cont'd 5) — RELEASE (project-only)

- **New command `RELEASE`** in `core.evolution.sk` (EP-66): MaiKS's own commit-and-push-to-
  `main` gate for an applied evolution — scope the APPLIED EPs since last push, re-run the
  CHECK sweep, decide the `ai_os_version` bump, one commit per EP, push (no PR). It is
  **project-only**, in the same class as `EVOLVE_BENCHMARK`. **Migration action for an
  installed project: none — and specifically do *not* add it.** `UPDATE_PROMPT.md` Step 3's
  merge exception already names `RELEASE` alongside `EVOLVE_BENCHMARK`: its
  `commands/index.json` entry, its string in `registry/index.json`'s
  `core.evolution.sk.commands`, and its `"release"`/`"ship"` aliases are never merged into
  an install, even though the update source ships all of them. An install that somehow
  already has it (hand-added) keeps it — not stripped retroactively.
- `core.evolution.sk/SKILL.md` gained the `### RELEASE` section and an `EVOLVE_APPLY` step 6
  pointer ("in this repo, finish by running `RELEASE`; in an installed project, follow the
  project's own VCS conventions"). That documentation copies in with the `registry/` sync
  and is harmless in an install (the command is unregistered there). No migration action.
- `rules/ultimate_rules.md`'s Project-Specific Addendum gained a "Framework Release
  Workflow" entry — purged on fresh install (Step 4 item 7) and preserved-not-merged on
  upgrade (Step 3a) like the rest of that block. No migration action.
- No `ai_os_version` bump — additive project-only content, consistent with the
  v2.1.0/EP-43 precedent.

## v2.7.0 (cont'd 4) — Epic/Story Planning, PLAN_RETRO

- **`core.planning.sk` gains epic decomposition** (EP-65): `PLAN_WRITE` can now write a
  large multi-piece initiative as an *epic* — one `memory/plans/<date>-<slug>.md` file with
  `Type: epic` in the header and `## Story` sections, each carrying its own
  `### Acceptance Criteria` and `### Steps`. Flat plans are unchanged — `Type:` absent means
  the exact behavior shipped in v2.7.0 (cont'd 3). `PLAN_EXECUTE` works stories in
  dependency order and re-derives the epic's roll-up `Status` and the `Active plan:`
  pointer's story count from checkbox state (never a stored counter). **Migration action:**
  none — additive skill content, covered by the `registry/` copy in `UPDATE_PROMPT.md`
  Step 3. Existing plan files stay valid (they're flat plans by the absent-`Type:` default).
- **New command `PLAN_RETRO`** (EP-65, alias `retro`): structured retrospective when an
  epic closes — appends a `## Retro` section to the epic plan file (delivered vs planned /
  what worked / what didn't / lessons → promotion candidates) and routes every lesson
  through `core.memory.sk`'s verify-before-promote gate rather than writing semantic memory
  itself. **Migration action:** merge the new entry into `commands/index.json`'s command
  list, add `"PLAN_RETRO"` to `core.planning.sk`'s `commands` array in `registry/index.json`,
  and add the `retro` alias to `commands/aliases.json` without dropping any the user added —
  all covered by the standard merge in `UPDATE_PROMPT.md` Step 3. No `manifest.json`
  `installed_skills` or `kernel/integrity.md` change (the skill was already registered).
- **Acceptance criteria feed the existing gate, no protocol edit** (EP-65): a story's
  `### Acceptance Criteria` list is consumed by `core.self-healing.sk`'s
  Verification-Before-Completion Protocol as its concrete checklist; the protocol itself is
  unchanged. `core.architect.sk` Phase 3a gained a one-line cross-reference noting its
  feature/AC block is the same shape. No migration action.
- No `ai_os_version` bump — additive skill/command content, no kernel edit, consistent with
  the v2.1.0/EP-43 precedent.

## v2.7.0 (cont'd 3) — Plans Folder, Skill-Invocation Banner

- **New memory location `.ai-os/memory/plans/`** (EP-64): dated standalone plan files,
  `plans/<YYYY-MM-DD>-<slug>.md`, written by `PLAN_WRITE` and `ARCHITECT_PLAN` instead of
  being inlined into the branch task file. Each carries a header
  (`Branch`/`Created`/`Status`/`Task file:`) plus `## Context` and a `## Steps` checklist;
  the plan file is the source of truth for execution progress, the task file keeps only a
  one-line `Active plan:` pointer. **Migration action:** ensure `.ai-os/memory/plans/`
  exists with a `.keep` (covered by `UPDATE_PROMPT.md` Step 2 item 1). Never delete or
  overwrite plan files already present. Existing installs simply have an empty `plans/`
  until the next `PLAN_WRITE`. Tracked, not gitignored — no `.gitignore` change.
- **Stray-host-plan handling redirected** (EP-64, revises EP-48): when a host force-creates
  `implementation_plan.md`/`walkthrough.md` outside `.ai-os/`, a *structured* plan is now
  moved into `plans/` with its shape intact rather than flattened into task notes; loose
  notes still append to the task file. Still gated on the two existing confirmations (ask
  before absorbing, ask separately before deleting the original). No migration action —
  behavior change in `BOOT.md` §2 step 4 and `core.memory.sk`, covered by the Step 3
  `BOOT.md`/`registry/` copy.
- **`PLAN_EXECUTE` / `TASK_CLOSE` / `MEMORY_CONSOLIDATE` updated** (EP-64): execute ticks
  checkboxes in the plan file; `TASK_CLOSE` sets the linked plan's `Status`;
  `MEMORY_CONSOLIDATE` gained a "Plan pruning" pass folding old `done`/`abandoned` plans
  into `plans/_summary.md`. No migration action — skill-file content, covered by the
  `registry/` copy.
- **Skill-invocation banner** (EP-63): `BOOT.md` §4 now has the agent emit a one-line
  `▸ AI-OS · {skill-id | "built-in"} · {COMMAND}` receipt before running any registered
  command's procedure. No migration action — `BOOT.md` content, covered by the Step 3
  copy. Self-report convention, not a hook.
- None of the above bumped `ai_os_version` — additive skill/command/kernel-text content and
  a new memory sub-directory, no compatibility break, consistent with the v2.1.0/EP-43
  precedent.

## v2.7.0 (cont'd 2) — Simplicity Skill, Subagent Boot-State Injection

- **New skill `core.simplicity.sk`** (`SIMPLIFY_REVIEW`/`SIMPLIFY_AUDIT`/`DEBT_LEDGER`,
  EP-58): pre-mutation simplicity ladder, the `AIOS-DEBT:` deliberate-shortcut marker
  convention, and review/audit passes scoped strictly to over-engineering. Adapted from
  `DietrichGebert/ponytail` (MIT). Migration action: copy the skill folder in (covered by the
  `registry/` copy in `UPDATE_PROMPT.md` Step 3), register in
  `registry/index.json`/`manifest.json.installed_skills`/`kernel/integrity.md`, and merge the
  four new `commands/aliases.json` shortcuts (`simplify`, `bloat`, `overengineered`, `debt`)
  without dropping any the user added themselves.
- **`AIOS-DEBT:` marker convention introduced** (EP-58). No migration action — an upgrading
  project simply has zero markers until someone writes one. `DEBT_LEDGER` on a fresh upgrade
  correctly reports `No AIOS-DEBT markers.`
- **Subagent governance** (EP-59/EP-60): `core.dev-loop.sk` Path A now requires dispatch
  prompts to carry governance context inline, and `.ai-os/scripts/session-start-hook.sh` gained
  an optional first argument (the hook event name, default `SessionStart`) so one script serves
  both `SessionStart` and the new `SubagentStart` entry in
  `templates/claude-code-hooks.json`. Session context does not propagate to dispatched agents —
  they are separate hook events for that reason.
  **Migration action:** every pre-v2.7.0(cont'd 2) install is missing the `SubagentStart` hook
  entry; `UPDATE_PROMPT.md` Step 5's unconditional Claude Code hook check adds it. The script's
  argument is optional and defaults to the old behavior, so an existing `SessionStart` entry
  keeps working unchanged and **must not be rewritten**. If the user narrowed their own
  `SubagentStart` matcher, leave their value alone.
- **Cost note for upgraders:** the `SubagentStart` hook injects ~26 KB (~6.5K tokens) on every
  subagent spawn. Narrow the matcher (it filters on agent type) rather than dropping the entry
  if that's too much for a given project.
- None of the above bumped `ai_os_version` — additive skill/command/script content, no
  kernel-content or compatibility change, consistent with the v2.1.0/EP-43 precedent.

## v2.7.0 (cont'd) — Planning & Dev-Loop Skills, Direct Boot-State Injection

- **New skill `core.planning.sk`** (`PLAN_BRAINSTORM`/`PLAN_WRITE`/`PLAN_EXECUTE`, EP-49):
  per-feature brainstorm → write-plan → execute cycle for work inside an existing project,
  distinct from `core.architect.sk`'s greenfield-only scope. Migration action: copy the
  skill folder in (covered by the `registry/` copy in `UPDATE_PROMPT.md` Step 3), register
  in `registry/index.json`/`manifest.json.installed_skills`/`kernel/integrity.md`.
- **New skill `core.dev-loop.sk`** (`DEV_IMPLEMENT_REVIEWED`, EP-53): implementation with a
  review pass — independent subagent review when the host genuinely supports subagent
  dispatch, an honestly-labeled same-agent structured fallback when it doesn't. Same
  migration action as above.
- **TDD Discipline section added to `core.testing.sk`** (EP-50), **Verification-Before-
  Completion Protocol added to `core.self-healing.sk`** (EP-51), **`INFRA_WORKTREE_START`/
  `INFRA_WORKTREE_FINISH` added to `core.infra.sk`** (EP-52) — additive content/commands on
  existing skills, no new files. Migration action: none beyond the standard `registry/`/
  `commands/` overwrite-merge in Step 3.
- **New `.ai-os/scripts/session-start-hook.sh`** (EP-56): the Claude Code `SessionStart`
  hook now injects `BOOT.md`/`ultimate_rules.md` content directly into context via
  `hookSpecificOutput.additionalContext` on `startup|clear|compact`, replacing the older
  `compact`-only echo-reminder version. Migration action: `UPDATE_PROMPT.md` Step 5's
  unconditional Claude Code hook check picks up both the new script (via the standard
  `.ai-os/` copy) and the widened `.claude/settings.json` matcher on any upgrade.
- None of the above bumped `ai_os_version` — additive skill/command/script content, no
  kernel-content or compatibility change, consistent with the v2.1.0/EP-43 precedent for
  pure additions.

## v2.7.0 — Session-Scoped Kernel Override

- **`R3` in `rules/ultimate_rules.md` gained a session-scoped bypass form**: alongside the
  existing per-action `KERNEL OVERRIDE AUTHORIZED: {files}`, a human can now grant
  `KERNEL OVERRIDE AUTHORIZED FOR SESSION: {scope}` — a standing grant for the rest of the
  session instead of re-authorizing every individual kernel edit. `{scope}` must be
  explicit (a file/glob list, or an explicitly-typed `*`) — never defaults to `*` on a bare
  invocation. Expires at 5 kernel edits under one grant (mirrors this file's own
  5-evolutions-per-conversation rate limit) or at session end (`WRAP`), whichever comes
  first; never carries into a new session.
- **New ephemeral file `.ai-os/memory/episodic/session_override.json`**: records the
  active grant (`scope`, `granted_ts`, `session_id`) read from disk, not from conversation
  memory — a `SessionStart`/compact-triggered re-read (see v2.6.0's Claude Code hook,
  EP-40 in `progress.md`) can't be relied on to preserve a grant claim made earlier in a
  paraphrased-away part of the transcript, so the check has to hit durable state instead.
  The grant itself gets one `decisions.jsonl` entry; every kernel edit made under it still
  logs its own entry per R13, unaffected.
- **`BOOT.md` §1 and §3, `rules/evolution_policy.md`'s Kernel Space section and DO step**
  updated to reference both override forms.
- **`INSTALL_PROMPT.md` Step 5**: added `session_override.json` to the ephemeral
  `.gitignore` block (per-machine/per-session state, same tier as `last_session.json`).
- Migration action: none for existing kernel content — `rules/ultimate_rules.md`,
  `BOOT.md`, and `evolution_policy.md` changes are covered by the standard overwrite in
  Step 3 (itself gated by this version's `KERNEL OVERRIDE`); `session_override.json` is
  created on demand on first use, nothing to seed. Existing installs pick up the
  `.gitignore` entry via `UPDATE_PROMPT.md` Step 5's existing generic gitignore-refresh
  check (already re-reads `INSTALL_PROMPT.md` Step 5's current list, no separate migration
  needed).

## v2.6.0 — Honesty Over Approval

- **New `R25` in `rules/ultimate_rules.md`** (Domain 11, BLOCKING, no archetype override):
  optimize for accuracy, not for the response the user wants to hear. A technically-true
  answer shaded toward flattery — emphasizing positives, omitting real weaknesses,
  softening a blunt conclusion, burying disagreement under caveats — violates this even
  with zero false claims. Extends R21 (claim verification) to emphasis/framing, not just
  factual accuracy.
- **`core.self-healing.sk`'s Response Credibility Protocol** gained a 7th checklist item,
  "Sycophancy Resistance," operationalizing R25 as something actually applied before each
  substantive response, not just a rule sitting in a reference file.
- **`BOOT.md` §3 digest table** updated with R25.
- Migration action: none — `rules/ultimate_rules.md`, `BOOT.md`, and
  `registry/core.self-healing.sk/SKILL.md` content changes, covered by the standard
  overwrite/merge in Step 3.

## v2.5.0 — AI-First Kernel Authoring, Evolution-Policy Fixes

- **`BOOT.md` and `rules/ultimate_rules.md` rewritten in dense, AI-first style**: fragments,
  arrows, pipe-lists instead of full connective prose — these files' actual readers are AI
  agents, not humans, so the tradeoff shifted from readability to unambiguous parsing +
  token cost. `ultimate_rules.md` dropped ~45% in word count across two compaction passes,
  `BOOT.md` ~29%. No rule/section numbering or behavior changed — verified programmatically
  (all 24 rule IDs, all 11 `BOOT.md` sections, every command/file cross-reference, the exact
  user-facing quoted conflict message all survived).
- **New standing rule in `rules/evolution_policy.md`**: future kernel-space content
  (`BOOT.md`, `rules/*.md`) is authored in this compact style from the start, not written
  readable-first and compacted in a later pass.
- **Fixed two real bugs found while adding that rule**: `evolution_policy.md`'s decision-log
  examples still showed the pre-EP-20 schema (`timestamp`/`id`/`status`/`details`) instead of
  the unified `{"ts","type","what","why","files"?}` shape — missed when EP-20 unified the
  schema everywhere else. And its "Forbidden Evolutions" #1 said modifying the file itself is
  "NEVER permitted, regardless of archetype or context," directly contradicting the same
  file's own Evolution Boundaries table three sections above, which says kernel files
  (including this one) CAN be modified with `KERNEL OVERRIDE AUTHORIZED`. Fixed both
  "modifying rules"/"modifying this file" items to explicitly require the override rather
  than reading as an absolute, no-exception ban.
- Migration action: none — `rules/*.md` and `BOOT.md` content changes, covered by the
  standard overwrite in Step 3 (gated by the v2.2.0 `KERNEL OVERRIDE` check).

## v2.4.0 — Blast-Radius and Root-Cause Rules

- **New `R23` (Blast-Radius Assessment for Wide-Reaching Changes)** and **`R24` (Root Cause
  Before Fix)** added to `rules/ultimate_rules.md` Domain 11. R23 extends R7's "assess risk
  before destructive ops" concept to non-destructive but widely-reaching changes (a shared
  utility, a schema field, an API contract) — use `INFRA_MAP_DATAFLOW` when the change traces
  to a specific field/entity, otherwise enumerate call sites manually, before scoping the
  implementation. R24 formalizes the debugging discipline already described operationally in
  `BOOT.md` §7 (diff-driven debugging, memory-traced debugging) as a rule: identify root
  cause before calling a fix done, log cause + affected scope together, verify against the
  actual blast radius (`TEST_IMPACT`) rather than guessing test scope.
- **`BOOT.md` §3's Rules Digest table updated**: R23 folded into the existing R7 digest row
  (same severity pattern), R24 folded into the existing advisory-rules row.
- **Project-Specific Addendum note fixed**: was still referencing "R1–R19" as the rules
  user-defined additions must not conflict with — already stale before this release (R20–22
  existed), now corrected to "R1–R24."
- Migration action: none — this is a `rules/ultimate_rules.md` and `BOOT.md` content change,
  covered by the standard overwrite in Step 3 (itself gated by the v2.2.0 `KERNEL OVERRIDE`
  check, so a user's own project-specific rule additions in the addendum section are safe).

## v2.3.0 — Retrospective Memory Amendment

- **New `MEMORY_AMEND` command** on `core.memory.sk`: corrects or retracts an existing
  `knowledge/*.md` entry that turned out to be wrong, or that was accurate but caused a bug
  when followed. `TASK_CLOSE`/`MEMORY_CONSOLIDATE` only ever add to semantic memory or
  delete something a *new* fact supersedes — neither one revisits an existing entry just
  because it was later found to be wrong, so a bad promotion previously had no path back to
  being corrected short of someone noticing it during an unrelated pass. Outcomes: correct
  in place (stale fact), relocate to `known_gotchas.md` (true but harmful advice — keep the
  lesson, discard the recommendation), or remove outright (diff-before-delete, same as the
  Forgetting Policy). Same archetype-scaled accept gate as any other semantic-memory write.
- **`BOOT.md` §7 (Self-Healing)** gained a "memory-traced debugging" bullet: when a bug's
  root cause traces back to a `knowledge/*.md` entry, run `MEMORY_AMEND` too, not just the
  code fix — the entry is still trusted ground truth for every other session and developer
  until it's corrected. `BOOT.md` §4 gained a matching natural-language routing callout
  ("that doc is wrong," "this caused the bug") so the match isn't missed the way the
  data-flow impact-analysis phrasing was in v2.2.0.
- Migration action: none — new command content, covered by the standard `registry/`/
  `commands/` merge in Step 3. The two `BOOT.md` additions are covered by the standard
  overwrite, now itself protected by v2.2.0's `KERNEL OVERRIDE` check.

## v2.2.0 — Task Memory on Every Branch, Lightweight WRAP, Data-Flow Tracing

- **Task memory now created on every branch, no exceptions except detached `HEAD`**:
  `main`/`master`/`develop`/`release/*` previously skipped task-file creation entirely and
  implicitly allowed writing straight to `project_knowledge.md` — that contradicted the
  verify/accept promotion gate enforced everywhere else. Protected branches now get a
  *rolling* task file, drained by `MEMORY_CONSOLIDATE`'s verify/accept gate instead of
  archived by `TASK_CLOSE`. A branchless workspace (detached `HEAD`, no git identity) checks
  for an existing open task first, and **always asks** the user what to call one if none
  exists — no silent skip, no invented name. Migration action: none for existing task files
  (they're still valid); going forward, expect a task file to exist even on protected
  branches, and see the corrected orphan-sweep exception in the v2.1.0 section below — ad-hoc
  named files are not orphans just because they lack a branch match.
- **New lightweight `WRAP` built-in**: session-summary write only (no promotion, no task/
  semantic memory writes) — added because the `wrap` alias previously pointed straight at
  `MEMORY_CONSOLIDATE`, meaning "let's take a break" could silently trigger full memory
  promotion. Migration action: `commands/index.json`'s new `WRAP` entry is covered by the
  standard Step 3 copy. **Force-correct `commands/aliases.json`'s `wrap` key specifically**
  even though that file is otherwise a preserve-the-user's-customizations merge target: if
  the user's existing value is `"MEMORY_CONSOLIDATE"` or the older broken
  `"LOG_DECISION && MEMORY_CONSOLIDATE"` chain, overwrite it to `"WRAP"` — this one key is a
  bug fix, not a customization worth preserving.
- **New `INFRA_MAP_DATAFLOW` command** (alias `trace`) on `core.infra.sk`: on-demand data-flow
  tracing (input field to every DB/API/queue/file/cache/email sink it reaches, or backward
  from a sink to its inputs) for bug triage and change-impact analysis. Migration action:
  none — new command content, covered by the standard `registry/`/`commands/` merge in Step 3.
- Bumped `ai_os_version` to `2.2.0` — the prior three evolutions (EP-28/29/30/31) shipped
  without a version bump, which meant `UPDATE_PROMPT.md` Step 4's old-vs-new version compare
  saw no newer sections to walk and skipped all of the above during upgrades. That's the
  actual root cause of an orphan-sweep bug a user hit testing the updater: without a version
  bump, the migration walk never reached the ad-hoc-exception fix above at all.

## v2.1.1 — Verified-Acceptance Gate for Memory Promotion

- **`core.memory.sk` TASK_CLOSE step 2 split into 2 + 2a**: step 2 (unchanged) verifies a
  candidate truth is factually accurate against the current repo state; new step 2a checks
  it was actually *accepted* — scans the task file for unresolved-problem markers
  (`TODO`/`FIXME`/`BUG`/`WIP`/etc.) near the claim, and gates the write on human
  confirmation scaled by archetype (reuses R15's existing override table: `hobby` promotes
  directly, `startup`+ requires explicit sign-off before writing to semantic memory).
- **Why**: a claim can be 100% factually accurate (the buggy code really does exist and
  behave that way) while still being exactly the kind of thing that shouldn't become
  permanent project truth. Verifying facts and verifying acceptance are different checks;
  v2.1.0 only had the first one.
- **`R15` in `ultimate_rules.md`** gained one bullet: promoting a task-memory claim to
  semantic memory is now explicitly listed as functionally irreversible.
- Migration action: none — this is a rules/skill content change, covered by the standard
  `BOOT.md`/`rules/`/`registry/` overwrite in `UPDATE_PROMPT.md` Step 3.

## v2.1.0 — Memory Lifecycle Hardening

- **New skill**: `.ai-os/registry/core.memory.sk/` — backs `TASK_CLOSE`/`MEMORY_CONSOLIDATE`
  with a real procedure (verify-before-promote, diff-before-delete, dedup, branch-name
  sanitization, orphan sweep, archive pruning). Migration action: copy the skill folder in
  (covered by the `registry/` copy in `UPDATE_PROMPT.md` Step 3), register it in the user's
  `registry/index.json` and `manifest.json.installed_skills`, add its path to
  `kernel/integrity.md`'s required-paths list if the user has a customized copy of that file.
- **Task-memory filename sanitization**: `memory/tasks/[branch].md` now sanitizes slashes and
  other path-unsafe characters in the branch name (`feature/x` → `feature_x`) instead of
  creating nested paths, and detached-HEAD state no longer collides on a literal `tasks/HEAD.md`.
  Migration action: if the user has existing task files with unsanitized names (nested dirs
  under `tasks/`, or a `tasks/HEAD.md`), leave them — they're still valid working files, just
  rename going forward.
- **Orphan sweep recommended**: sweep `tasks/*.md` against `git branch -a` during the upgrade
  (handled generically by `UPDATE_PROMPT.md` Step 4's migration walk) rather than waiting for
  the next `MEMORY_CONSOLIDATE`. Safe to re-run — the sweep is conditional on the checks
  below, so a repeat pass re-evaluates and moves nothing new. **A task file with no matching
  branch is not automatically an orphan** — as of v2.2.0, ad-hoc task files (opened when
  there's no git identity, named after what the user called the task rather than a branch)
  are expected to have no branch match by design. Only move a file to `archived_tasks/` if
  it has no matching branch *and* shows no sign of being an active ad-hoc task (recently
  modified, or referenced in recent `sessions.jsonl` entries) — when in doubt, leave it for
  the next `MEMORY_CONSOLIDATE` to judge rather than archiving it during an upgrade on a
  branch-match check alone.
- **Installer purge scope widened**: `INSTALL_PROMPT.md` Step 3 now also purges
  `.ai-os/memory/tasks/*.md` and `.ai-os/memory/archived_tasks/*.md` (except `.keep`) on fresh
  installs — a stray framework-development task file was previously shipping into new installs.
  No migration action for existing users; this only affects the install flow.

## v2.0.0 — Boot Slimming & Log Schema Unification

- **BOOT.md restructured**: went from one ~25KB monolith to a ~7KB hot core (§1-§11 kept,
  but detail moved out) plus two new on-demand files. Migration action: overwrite the
  user's `BOOT.md` with the new version (Step 3 already does this); no memory content is
  affected, this is kernel space only.
- **New kernel file**: `.ai-os/kernel/bootstrap.md` (the First-Boot wizard, moved out of
  BOOT.md §10). Migration action: copy it in if missing (covered by the `kernel/` directory
  copy in `UPDATE_PROMPT.md` Step 3).
- **New episodic file**: `.ai-os/memory/episodic/last_session.json` — a single-entry session
  summary read at boot instead of scanning all of `sessions.jsonl`. Migration action: if
  missing, create it from the last entry in the user's existing `sessions.jsonl` (or an
  empty placeholder if `sessions.jsonl` is empty). Do not overwrite if it already exists.
- **Log schema unified**: `decisions.jsonl` entries now use one shape —
  `{"ts","type","what","why","files"?}` — replacing the four different shapes
  (`decision`/`rationale`/`confidence`/`alternatives_considered`/`outcome`/`references`,
  `action`/`reason`/`files_affected`/`reversible`/`session_id`, etc.) that had accumulated.
  Migration action: **do not rewrite the user's historical entries** — old-shape lines
  remain valid history. Only new entries written going forward use the new schema.
- **`registry/index.json` schema simplified**: removed the per-skill `circuit_breaker`,
  `failure_count`, `last_invoked` fields — nothing was reliably maintaining them, so
  `HEAL_CIRCUIT_STATUS` now derives skill health from `decisions.jsonl` on demand instead.
  Migration action: if the user's `registry/index.json` has custom skills with these
  fields, it's safe to leave them (extra keys are harmless) or strip them for consistency.
- **Rule R4 (persona prefix) demoted** from BLOCKING to ADVISORY, and R5/R16 (token/step
  limits) reframed from enforced counters to best-effort heuristics, since an agent cannot
  reliably self-instrument exact token or step counts. No file migration needed — this is
  a `rules/ultimate_rules.md` content change, covered by the Step 3 overwrite.

## v1.0.0
- **Four-Tier Memory Layout Migration**: 
  - Subdirectories added: `semantic/`, `episodic/`, `procedural/`, `tasks/`, `archived_tasks/`
  - Migration action: Move files from `.ai-os/memory/` root to subdirectories (see `UPDATE_PROMPT.md` Step 2).
  - Clean up: After verifying the files are successfully copied/moved to their respective subdirectories, delete the obsolete root-level files in `.ai-os/memory/` (specifically `project_knowledge.md`, `decisions.jsonl`, and `sessions.jsonl` if they remain in the root) to prevent duplicate context loading.
- **Indexed Semantic Knowledge Segregation**:
  - Subdirectory added: `.ai-os/memory/semantic/knowledge/`
  - Migration action: If the upgrading user has a monolithic `project_knowledge.md`, parse and segregate its sections into individual files (`architecture_overview.md`, `conventions_patterns.md`, `known_gotchas.md`, etc.) under `semantic/knowledge/`, then convert `project_knowledge.md` into the index document referencing those sub-files (see `UPDATE_PROMPT.md` Step 2).


