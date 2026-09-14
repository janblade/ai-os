---
name: planning
description: >-
  Per-feature brainstorm -> write-plan -> execute cycle for work inside an
  existing project. Clarifies scope through small rounds of questions, writes
  an implementation plan concrete enough to execute without re-deriving
  intent, then works it step by step with verification at each step. A large
  multi-piece initiative is written as an epic (one plan file, story sections
  with their own acceptance criteria); PLAN_RETRO closes an epic with a
  structured lessons pass.
---

# Planning — Brainstorm, Write, Execute

## Overview

`core.architect.sk` handles the greenfield case: an idea with no project yet, interviewed
and scaffolded once at genesis. This skill handles the far more common case — a feature or
fix requested *inside* an existing project — with the same discipline (clarify before
designing, write the plan down, don't wing execution) applied per task instead of once per
project. The two skills don't overlap: architect.sk triggers when there's no project;
this skill triggers on ordinary feature/bugfix requests within one that already exists.

Not every request needs this. A granular action (fix a typo, rename a variable, answer a
question) doesn't match anything here — use normal tools directly, same rule `BOOT.md` §4
already states for command matching in general. This skill is for units of work substantial
enough that skipping straight to code risks building the wrong thing or losing track of
steps partway through.

Most work is one flat plan. A large initiative that splits into several independently
shippable pieces gets an **epic** instead — one plan file with `## Story` sections, each
carrying its own acceptance criteria and steps (`PLAN_WRITE` step 3 decides which). This is
`core.architect.sk` Phase 3's feature/story/acceptance-criteria decomposition applied to
in-project work instead of greenfield — same shape, same discipline, per task. `PLAN_RETRO`
closes an epic with a structured lessons pass.

## Dependencies

- `core.observability.sk` — decision logging for plan approval and step completion
- `core.testing.sk` — TDD discipline governs how each execution step gets verified
- `core.self-healing.sk` — Verification-Before-Completion Protocol gates each step, each
  story's acceptance criteria, and the final report
- `core.memory.sk` — `PLAN_RETRO`'s lesson candidates route through its verify-before-promote
  gate (steps 2/2a/4); `TASK_CLOSE`/`MEMORY_CONSOLIDATE` prune closed plan files
- `core.dev-loop.sk` — its **Review Pass** sub-procedure runs as an independent second
  opinion on the diff: once per flat plan at completion, once per epic story at the
  story-done gate. `PLAN_EXECUTE` implements in-thread, so it calls the Review Pass only,
  not `DEV_IMPLEMENT_REVIEWED` whole (which also dispatches an implementer subagent)
- `core.simplicity.sk` — its **Simplicity Ladder** runs before writing each step's code
  (`PLAN_EXECUTE` step 2), at the project's archetype-derived intensity; this skill
  otherwise had no caller in the plan path (EP-70)

## Commands

### PLAN_BRAINSTORM

Clarify a feature's scope before any design or code.

```
> OS_COMMAND PLAN_BRAINSTORM --feature="<description in plain language>"
```

**Procedure:**
1. Restate understanding in one sentence: "Here's what I think you're asking for: [...].
   Is that right?"
2. Ask 2-3 clarifying questions per round, not all at once — acceptance criteria, edge
   cases, what's explicitly out of scope, how it should fail.
3. Check the active task file (`memory/tasks/*.md`) for constraints or conventions already
   established this task before asking — don't re-ask what's already known.
4. Completion criteria — move to `PLAN_WRITE` when you can state: what the feature does in
   one sentence, its acceptance criteria, and what's explicitly excluded.
5. Write the outcome to the active task file's working notes (task memory, per `BOOT.md`
   §9's routing rule — never straight to semantic memory).

---

### PLAN_WRITE

Turn a clarified feature into a concrete, ordered implementation plan.

```
> OS_COMMAND PLAN_WRITE [--feature="<description>"]
```

**Procedure:**
1. **Check for a reusable workflow.** Read `memory/procedural/workflows.json` for an
   entry whose `trigger` matches this request. Match → present it as a starting point
   (adapt its `steps` rather than drafting from scratch), tell the user which workflow
   matched. If the user proceeds with it, bump that entry's `success_count` and
   `last_used` when the plan is later written (step 7). No match → continue as normal.
2. If the request is non-trivial and `PLAN_BRAINSTORM` hasn't run this task yet, run it
   first (or ask the user if they'd rather skip straight to planning).
3. **Decide the form — flat plan or epic.** Epic only when **all** hold: the work splits
   into 2–5 pieces that each deliver independently shippable, separately-verifiable value
   (each could ship alone against its own acceptance criteria); the pieces run in an
   independent or explicitly-stated dependency order; and a single flat step list would
   exceed ~15 steps or mix unrelated verification surfaces. Otherwise flat. Unsure → ask
   the user "one plan, or an epic with N stories?" State the decision and the story list in
   one line — same match-once discipline as `BOOT.md` §4.
4. Break the work into discrete, ordered steps (flat plan), or per story into acceptance
   criteria + steps (epic). Each step must be concrete enough that a literal-minded
   executor doesn't need to re-derive intent — name specific files/functions where already
   known, not just "update the backend."
5. For each step that changes behavior, note how it gets verified (which test, which
   manual check) — ties directly into `core.testing.sk`'s TDD discipline: a step that adds
   behavior should name the test that proves it, written before the implementation. For an
   epic, each story also gets an `### Acceptance Criteria` block (2–5 observable,
   independently-testable `[ ]` items) — same checkbox shape as `core.architect.sk` Phase
   3a's decomposition block. That list is the story's verification contract: `PLAN_EXECUTE`
   runs it through `core.self-healing.sk`'s Verification-Before-Completion Protocol before
   the story is `done`, and an item that can't be exercised is disclosed per that
   protocol's step 4, never ticked silently.
6. Present the full plan (flat) or the whole epic — every story, every acceptance criterion
   — to the user. Wait for approval before `PLAN_EXECUTE` starts — same "present, wait for
   approval" pattern as `core.architect.sk`'s Phase 2/3.
7. Write the approved plan to its own file: `memory/plans/<YYYY-MM-DD>-<slug>.md`, where
   `<slug>` is a short kebab-case name from the feature (`add-pkce-flow`, not the whole
   sentence) and `<YYYY-MM-DD>` is today. Reused a workflow at step 1 → update that
   `workflows.json` entry's `success_count`/`last_used` now.

   **Flat plan:**
   ```markdown
   # Plan: <one-line title>
   - Branch: <sanitized branch name, or "none">
   - Created: <YYYY-MM-DD>
   - Status: approved          # draft | approved | in-progress | done | abandoned
   - Task file: memory/tasks/<name>.md

   ## Context
   <the one-paragraph PLAN_BRAINSTORM outcome — what it does, acceptance criteria,
   what's explicitly out of scope>

   ## Steps
   1. [ ] <step> — verify: <the test or check from procedure step 5>
   2. [ ] ...
   ```

   **Epic** — same file, add `Type: epic` to the header, and replace `## Steps` with
   `## Story` sections. `## Context` carries epic-level acceptance criteria (what "epic
   done" means beyond the sum of stories) plus out-of-scope. Story `Status:` uses the same
   enum as the header.
   ```markdown
   # Epic: <one-line title>
   - Branch: <...>
   - Created: <YYYY-MM-DD>
   - Status: approved          # DERIVED roll-up once execution starts — see PLAN_EXECUTE
   - Type: epic                 # omit (or "plan") for a flat plan
   - Task file: memory/tasks/<name>.md

   ## Context
   <what the epic delivers; epic-level acceptance criteria; out of scope>

   ## Story 1: <kebab-slug> — <title>
   Status: approved
   ### Acceptance Criteria
   - [ ] <observable, independently testable criterion>
   ### Steps
   1. [ ] <step> — verify: <test/check>

   ## Story 2: <kebab-slug> — <title>
   Status: approved
   depends on: Story 1          # optional
   ### Acceptance Criteria
   - [ ] ...
   ### Steps
   1. [ ] ...
   ```

   This file is the single source of truth for both the plan and its execution progress.
   In the active task file, write only a one-line pointer — never a second copy of the
   steps:
   - flat: `Active plan: memory/plans/<file>.md (approved, 0/<N>)`
   - epic: `Active plan: memory/plans/<file>.md (epic approved, 0/<N> stories)`

   Plans are not gitignored; they're shared project artifacts like the task file itself.

---

### PLAN_EXECUTE

Work an approved plan step by step.

```
> OS_COMMAND PLAN_EXECUTE [--plan=<plan_file>]
```

**Procedure:**
1. Load the plan file — the one named by the active task file's `Active plan:` pointer, or
   the path given in `--plan`. **Flat plan:** set `Status:` to `in-progress`. **Epic**
   (`Type: epic`): the active story is the lowest-numbered story not `done` whose
   `depends on` stories are all `done`; set that story's `Status:` to `in-progress`.
2. Execute one step at a time. Before writing a step's code, apply `core.simplicity.sk`'s
   Simplicity Ladder — stop at the first rung that holds — at the project's
   archetype-derived intensity (`core.simplicity.sk`'s Intensity table; no separate flag on
   the plan itself). After each step, run its verification (per `PLAN_WRITE` step 5 and
   `core.self-healing.sk`'s Verification-Before-Completion Protocol) before moving to the
   next — don't batch verification to the end.
3. Check off each step (`[ ]` → `[x]`) in the plan file as it completes. **Epic story-done
   gate:** when every step in the active story is `[x]`, run that story's
   `### Acceptance Criteria` through the Verification-Before-Completion Protocol — tick
   each criterion `[ ]` → `[x]` only when a run or exercise actually confirms it; disclose
   an unverifiable one per that protocol's step 4. Then run `core.dev-loop.sk`'s **Review
   Pass** on that story's diff (`git diff` for its steps) with the story title +
   `### Acceptance Criteria` as the spec — emit one line naming the branch taken
   (`independent reviewer` / `self-review fallback`), surface its findings to the user,
   non-blocking (it is a second opinion, not a gate). Then set the story `Status: done` and
   move to the next eligible story (step 1).
4. **Refresh the roll-up — always re-derived, never a stored counter.** After any checkbox
   or story-status change, recompute: (flat) the `Active plan:` pointer's `N/M` step count;
   (epic) each `## Story` `Status:` line from its checkbox state, the epic header `Status:`
   (`approved` = all stories approved, none started; `in-progress` = any story started or
   any box checked; `done` = every story `done`; `abandoned` = closed with stories
   outstanding), and the pointer's `N/M stories` = count of `done` stories. Active-story
   step detail is never mirrored into the pointer — it's read from the plan file.
5. A step or story turns out wrong, blocked, or reveals the plan itself was mistaken →
   stop, don't silently improvise past it. Surface it to the user rather than guessing
   (R24: confirm before applying a fix when confidence is below High). Never auto-upgrade a
   flat plan into an epic mid-execution — stop and re-plan through `PLAN_WRITE`. A single
   story may be set `Status: abandoned` with user approval; the epic then finishes on the
   rest or is itself `abandoned` at `TASK_CLOSE`.
6. All steps done (flat) / all stories `done` and epic-level acceptance in `## Context`
   verified (epic) → run `core.dev-loop.sk`'s **Review Pass** once on the full accumulated
   diff with the plan's `## Context` as the spec (**flat plan only** — an epic reviewed
   each story at its step-3 gate, so no repeat sweep here); emit one line naming the branch
   taken, surface findings, non-blocking. Then set the plan file's `Status:` to `done`,
   report completion through the Verification-Before-Completion Protocol (not a bare
   "done"), and for an epic offer `PLAN_RETRO`. The plan file stays in `memory/plans/` as a
   dated record — `TASK_CLOSE`/`MEMORY_CONSOLIDATE` handle its eventual pruning
   (`core.memory.sk`), not this command.
7. **Offer to save a reusable workflow — only if the pattern is genuinely repeatable for
   this project**, not a one-off feature. Ask the user; on yes, append to
   `memory/procedural/workflows.json`, matching its existing schema: `id` (kebab-slug),
   `name`, `description`, `trigger` (when to reuse this — the pattern `PLAN_WRITE` step 1
   will later match against), `steps` (each plan step generalized past this one instance
   — `action`, `tool`, `success_criteria`; `parameters` only when the step's tool takes
   structured flags, e.g. an `OS_COMMAND` invocation, omitted otherwise; `fallback` left
   `null` if none observed), `learned_from` (this plan's file path), `success_count: 1`,
   `last_used` (now), `pinned: false`, `project_only` (`true` only if this pattern is
   specific to this repo's own dev process and must never reach an installed project —
   `false`/omitted for a normal project workflow; EP-75). Skip silently for one-off work
   — most plans are not reusable patterns, and a `workflows.json` full of one-time features
   would make step 1's
   matching noise, not signal.

---

### PLAN_RETRO

Structured retrospective when an epic plan closes. Epic-scoped — a flat plan's lessons go
through the normal `TASK_CLOSE`/`MEMORY_CONSOLIDATE` path, not this command.

```
> OS_COMMAND PLAN_RETRO [--plan=<plan_file>]
```

**Trigger:** an epic reaches `Status: done`, or is closed `abandoned` with 2+ stories that
had completed work. `PLAN_EXECUTE` step 6 and `TASK_CLOSE` (when the linked plan is an
epic without a `## Retro` section) both offer it; the user can also invoke it directly or
by natural language ("retro on the checkout epic", "what did we learn from that epic").

**Procedure:**
1. Resolve the epic plan file (pointer or `--plan`). Not `Type: epic` → tell the user retro
   is epic-scoped and offer normal consolidation instead.
2. Assemble the span, all on-demand reads (no stored retro state):
   - the epic file — stories `done`/`abandoned`/added mid-flight, acceptance criteria that
     ended unmet, steps added or dropped;
   - `memory/episodic/decisions.jsonl` — entries from the epic's `Created:` date to now
     whose `what`/`files` reference the plan path or the branch task file;
   - the branch task file's working notes;
   - `git log <fork-point>..HEAD` for the branch, if there is one.
3. Write a terse `## Retro` section appended **inside the epic plan file** (not a sidecar),
   four headings:
   - **Delivered vs planned** — stories done/abandoned/added; acceptance criteria that
     shipped unmet, with why.
   - **What worked** — practices/decisions to repeat, each traceable to a `decisions.jsonl`
     line or a diff.
   - **What didn't** — friction, rework, mis-specified steps, scope misjudgements, each
     with evidence.
   - **Lessons → candidates** — generalizable statements proposed for promotion, each
     tagged with a destination (`knowledge/conventions_patterns.md` /
     `knowledge/known_gotchas.md` / `procedural/playbooks.md` / "epic-local, don't
     promote").
4. **Promote nothing directly.** `PLAN_RETRO` writes only the `## Retro` section. Each
   "Lessons → candidates" item is fed through `core.memory.sk` steps 2/2a/4 (re-verify
   against current repo state, confirm the underlying change was accepted not just closed,
   dedup, archetype-scaled accept gate) — run now if the user is closing out, else at the
   next `TASK_CLOSE`/`MEMORY_CONSOLIDATE`. The `## Retro` section is an *input* to that
   gate, never a bypass.
5. Log: `{"ts":"…","type":"decision","what":"PLAN_RETRO: <slug> — N lessons proposed","why":"epic closed","files":["memory/plans/<file>"]}`.

---

## Common Mistakes

1. **Skipping brainstorm on a "small" feature** — scope that turns out to have a hidden
   edge case is the exact failure mode `PLAN_BRAINSTORM` exists to catch before code is
   written, not after.
2. **Writing a plan too vague to execute** — "improve the auth flow" is not a step; "add
   rate-limiting to `POST /login`, capped at 5/min per IP, test: 6th request in a minute
   returns 429" is.
3. **Marking a step done without verifying it** — defeats the point of splitting execution
   into steps in the first place; see `core.self-healing.sk`'s Verification-Before-
   Completion Protocol.
4. **Reaching for an epic on ordinary work** — the epic form is for a genuine multi-piece
   initiative (`PLAN_WRITE` step 3's three-part test). A two-story "epic" where the stories
   aren't independently shippable is just a flat plan with extra headers. When in doubt,
   flat.
5. **Treating a `## Retro` as a promotion** — `PLAN_RETRO` proposes lesson candidates; it
   does not write semantic memory. Promotion still goes through `core.memory.sk`'s gate.
6. **Expecting `PLAN_EXECUTE` to catch its own implementation errors** — step 2's
   verification and the Verification-Before-Completion Protocol are both self-checks. The
   independent second opinion is `core.dev-loop.sk`'s Review Pass, which `PLAN_EXECUTE`
   runs once per flat plan and once per epic story (EP-67); before that it only ran when
   `DEV_IMPLEMENT_REVIEWED` was invoked by name.
7. **Treating an approved plan as license to skip the Simplicity Ladder** — a step being
   pre-approved decides *what* to build, not *how*. The ladder still governs each step's
   implementation choice (reuse vs. new code, stdlib vs. hand-rolled) at `PLAN_EXECUTE`
   step 2 (EP-70); before that it only ran when `SIMPLIFY_REVIEW`/`SIMPLIFY_AUDIT` was
   invoked by name, post-hoc on a diff that already existed.
8. **Saving every completed plan as a `workflows.json` entry** — `PLAN_EXECUTE` step 7
   (EP-74) is a judgment call, not a habit. Most feature work is one-off; a workflow
   entry is only worth writing when the *pattern* (not this specific feature) would
   genuinely recur. A file full of one-time plans makes `PLAN_WRITE` step 1's matching
   noise instead of signal — skip silently far more often than not.
