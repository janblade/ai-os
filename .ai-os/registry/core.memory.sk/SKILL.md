---
name: memory-lifecycle
description: >-
  Backs the built-in TASK_CLOSE and MEMORY_CONSOLIDATE commands with a real
  procedure. Governs the task -> archived -> semantic promotion pipeline:
  verifying claims before they become permanent, not silently dropping
  concurrent branches' work, deduplicating instead of accumulating, and
  sweeping up what falls through the cracks (orphaned task files, unbounded
  archives).
---

# Memory Lifecycle

## Overview

`TASK_CLOSE` and `MEMORY_CONSOLIDATE` are built-in commands (available even without this
skill installed — see `BOOT.md` §4), but without this skill their procedure is just a
couple of bullet points, which is thin enough to create real gaps: unverified claims
promoted to permanent memory, silent data loss when two branches touch semantic memory
concurrently, duplicate entries, and orphaned files nothing ever revisits. This skill is
where that procedure actually lives. `MEMORY_AMEND` (below) is not a built-in — it only
exists when this skill is installed — and covers the direction those two don't: correcting
or retracting an existing entry that turned out to be wrong, rather than adding a new one.

Neither command is this skill's concern when someone just wants to pause — that's `WRAP`
(session-summary write only, no promotion, not documented here because there's nothing to
verify or gate). Don't let "wrap up for the day" get routed to `MEMORY_CONSOLIDATE` — that
was a real bug (fixed) where the `wrap` alias pointed at full consolidation, meaning taking
a break could silently promote whatever happened to pass the accept gate at that moment.

The verify-before-promote / accept-gate / dedup discipline below isn't exclusive to these
two commands, either — it's the standard for *any* write into `project_knowledge.md` or
`knowledge/*.md`, wherever it originates. A skill command that derives a finding straight
from the codebase (e.g. `core.infra.sk`'s `INFRA_MAP_DATAFLOW`, which can resolve a custom
sink pattern worth remembering) follows the same steps 2/2a/4 here rather than writing
directly — a mechanically-derived fact still needs the accept gate, since the *distillation*
of what's worth keeping is a judgment call even when the underlying data is accurate.

## Dependencies

- `observability.sk` — decision logging

## Commands

### TASK_CLOSE

```
> OS_COMMAND TASK_CLOSE [branch-or-task-name]
```

Defaults to the current branch (`git rev-parse --abbrev-ref HEAD`), or the open ad-hoc task
name if there's no git identity (§2 step 4). If given explicitly and it does **not** match
the current branch/task, confirm with the user before touching that file — don't silently
archive a task that isn't the one you're on.

**Procedure:**
1. **Resolve the task file.** Derive the filename the same way it was created (see
   `BOOT.md` §2 step 4's sanitization rule): slashes and other path-unsafe characters in
   the branch name become `_`, so `feature/oauth-fix` → `tasks/feature_oauth-fix.md`, not
   a nested path. For an ad-hoc task (no git identity), use the name it was opened under.
2. **Verify facts before promoting.** For each candidate "confirmed truth" in the task
   file, re-check it against the actual current repo state (read the file, grep the
   symbol, run the check) before writing it to semantic memory — don't promote a claim
   from task notes just because it's written down. This is R21 applied at the
   highest-stakes point in the system: once something lands in `project_knowledge.md`,
   every future session on every branch treats it as ground truth without re-deriving it.
   **This alone is not enough** — a claim can be perfectly factually accurate and still
   describe a buggy, reverted, or not-yet-accepted design (step 2a).
2a. **Confirm the underlying work was actually accepted, not just closed.** "Factually
   verified" and "correct/accepted" are different things — a candidate truth can pass
   step 2 (the code it describes really exists) while still describing an approach that's
   broken or mid-revision:
   - **Scan for unresolved-problem markers** in the task file near each candidate truth
     (`TODO`, `FIXME`, `BUG`, `known issue`, `doesn't work`, `WIP`, `broken`, `revert`,
     case-insensitive). If present, don't promote that item — leave it in the task file.
   - **Gate on human sign-off, scaled by archetype (same table as R15)**: before writing,
     list the specific facts about to be promoted.
     - `hobby`: promote directly if step 2/2a pass, log for review.
     - `startup`/`enterprise`/`critical`: show the list to the user and get explicit
       confirmation before writing — do not treat "the task branch reached TASK_CLOSE" as
       itself sufficient sign-off. Prefer running `TASK_CLOSE` after the branch is actually
       merged (or the user explicitly says the task is done) over mid-task or on an
       abandoned experiment.
   - If a fact fails 2a but passed 2, it's real but not yet trustworthy framework-wide —
     leave it in the task file (or `archived_tasks/` when archiving) rather than promoting
     it as a stopgap; it can be promoted later once actually accepted.
3. **Diff before deleting.** If applying the Forgetting Policy (deleting something you
   believe is superseded) in `knowledge/*.md`: check `git log`/`git merge-base` for that
   file since this branch's fork point. If the entry you're about to delete was added
   *after* your fork point (i.e., by a different branch that merged first), don't delete
   it — you don't have full context on it. Flag the apparent conflict to the user instead.
4. **Dedup before appending.** Before adding a new entry to a `knowledge/*.md` sub-file,
   scan that file for an existing entry covering the same fact. If found, update it in
   place instead of appending a near-duplicate. Route to the sub-file whose *existing*
   domain it matches (`architecture_overview.md` / `conventions_patterns.md` /
   `known_gotchas.md`) — only create a new domain file if nothing existing fits, and
   register it in `project_knowledge.md`'s index when you do.
5. **Archive.** Move `tasks/[file].md` → `archived_tasks/[file].md`. If the task file's
   `Active plan:` pointer names a plan in `memory/plans/`, set that plan's `Status:` to
   `done` (steps finished) or `abandoned` (task closed with steps outstanding). If that
   plan is `Type: epic` and has no `## Retro` section yet, offer `PLAN_RETRO` before
   archiving — its lesson candidates then feed steps 2/2a of this same procedure. Leave the
   plan file in `memory/plans/` — it's a dated record; step 6 and `MEMORY_CONSOLIDATE`
   handle its eventual pruning, not this step.
6. **Prune the archive.** If `archived_tasks/` now has more than ~20 files, or files
   clearly older than a few months of project history, fold the oldest ones into a single
   `archived_tasks/_summary.md` (one line each: date, branch, one-sentence outcome) and
   delete the originals. `archived_tasks/` is a record of *that something happened*, not a
   full-text archive that needs to grow forever — nothing else in the system reads
   individual archived files back.
7. **Log and report.** Append to `decisions.jsonl` (schema in `BOOT.md` §9), write the
   session summary per `BOOT.md` §9's wrap protocol.

---

### MEMORY_CONSOLIDATE

```
> OS_COMMAND MEMORY_CONSOLIDATE
```

Same verify/accept/diff/dedup rules as `TASK_CLOSE` steps 2, 2a, 3, 4 apply here when
extracting episodic decisions into semantic knowledge — a `decisions.jsonl` entry
describing a fix that was later reverted is just as promotable-by-mistake as a buggy task
note. Four additions specific to this command:

**Drain rolling task files on protected branches**: every branch has a task file (`BOOT.md`
§2 step 4 — main/master/develop/release included, there's no branch where working notes
skip straight to a permanent tier). Ticket branches close theirs explicitly via
`TASK_CLOSE`. Protected branches never get a "done" event, so their task file is treated as
*rolling*: on every `MEMORY_CONSOLIDATE`, run `TASK_CLOSE` steps 2/2a/3/4 against it, then
clear it back to empty (don't move it to `archived_tasks/` — it isn't a finished ticket,
it's ongoing scratch space that just got drained). If nothing in it passes the accept gate
yet, leave it as-is and don't force a promotion.

**Orphan sweep** (run every time this executes, cheap): list `tasks/*.md` and compare
against `git branch -a`. Any task file whose branch no longer exists locally or remotely is
orphaned — move it to `archived_tasks/` with a one-line note ("orphaned — branch deleted
without TASK_CLOSE") rather than leaving it to accumulate untouched. Ad-hoc task files (no
matching branch by design) aren't orphans by this check — match them against the sanitized
name they were opened under instead; only flag one as stale if it hasn't been touched in a
long time and no session has referenced it. Do not attempt to extract semantic truths from
an orphaned file automatically — an abandoned branch's working notes may describe a design
that was rejected, not confirmed; surface it to the user instead if it looks substantive.

**Episodic rotation**: after extracting lessons, move the processed `decisions.jsonl` lines
to `decisions.archive.jsonl` (per `BOOT.md` §9) rather than leaving them to accumulate.

**Plan pruning** (run every time, cheap): list `memory/plans/*.md`. Any plan with
`Status: done` or `Status: abandoned` and a `Created:` date older than the same window
step 6 of `TASK_CLOSE` uses for `archived_tasks/` (~a few months, archetype-scaled) → fold
into `memory/plans/_summary.md` (one line each: date, slug, final status; for an epic, add
`epic — retro captured` or `epic — no retro`) and delete the original. The `## Retro`
section of an epic is pruned with its file — acceptable because its lessons already passed
or were explicitly denied `core.memory.sk`'s promotion gate at retro time. Plans still
`draft`/`approved`/`in-progress` are left alone regardless of age — an old open plan is a
signal, not clutter. A plan whose `Task file:` no longer exists and that isn't
`done`/`abandoned` → flag to the user, don't auto-prune.

---

### MEMORY_AMEND

```
> OS_COMMAND MEMORY_AMEND --file=<knowledge/*.md path> [--reason=<why>]
```

The promotion pipeline (`TASK_CLOSE`/`MEMORY_CONSOLIDATE`) only ever adds to semantic
memory or deletes something a *new* fact supersedes. Neither one revisits an existing entry
just because it turned out to be wrong — there is no other trigger that does either, so a
bad promotion just sits there, permanently trusted, until this command is run against it.
Two triggers: `BOOT.md` §7's memory-traced debugging (a bug's root cause traced back to a
knowledge-file entry), or a direct human report ("that convention is wrong," "the docs are
outdated on this").

**Procedure:**
1. **Identify the specific claim** being challenged — not the whole file, the specific
   sentence/bullet that's wrong or that recommended what caused the problem.
2. **Verify the claim is actually responsible** before touching anything — re-check it
   against current repo state the same way step 2 of `TASK_CLOSE` verifies a promotion,
   just in reverse: confirm it's now inaccurate, or confirm the bug/reason genuinely traces
   to following it. Don't amend on a hunch.
3. **Pick the outcome** — these are different, don't default to deletion:
   - **Correct in place**: the claim was accurate once but is now stale (code moved on).
     Update the entry to reflect current reality. Same dedup rule as promotion — edit the
     existing entry, don't append a second one.
   - **Relocate to `known_gotchas.md`**: the claim was *true* and following it still caused
     the problem — that's not a fact to erase, it's a gotcha to record. Move/rewrite it as
     an explicit "we used to do X, it caused Y, do Z instead" entry. Deleting this outright
     throws away the one thing worth keeping — the lesson.
   - **Remove outright**: the claim was simply wrong from the start and carries no ongoing
     lesson — delete it, same diff-before-delete discipline as the Forgetting Policy
     (check `git merge-base` before removing anything another branch may have added since).
4. **Accept-gate the amendment**, same archetype-scaled confirmation as any other write into
   semantic memory (R15's table, generalized to any writer — see this skill's Overview):
   `hobby` applies it directly and logs it; `startup`/`enterprise`/`critical` show the
   proposed amendment and get explicit confirmation before writing, same as a promotion —
   correcting a shared fact that other sessions and other developers are relying on is at
   least as high-stakes as adding one.
5. **Log distinctly.** Append to `decisions.jsonl` framed as an amendment, not a promotion —
   include what was wrong, what changed, and the reason (bug reference, or who reported it).
   This audit trail is what lets a future session understand *why* a "confirmed truth" got
   walked back, instead of just seeing it silently replaced.

---

### Absorbing Stray IDE Planning Artifacts

`AGENTS.md`'s Minimum Contract item 5 says don't create IDE-specific planning artifacts
(`task.md`, `implementation_plan.md`, `walkthrough.md`) — use `.ai-os/memory/tasks/`
instead. Some hosts create one anyway, forced by their own planning-mode hook rather than
the agent's choice (the reason EP-1 exists at all). When `BOOT.md` §2 step 4 notices one
of these sitting outside `.ai-os/` for the branch/task currently being loaded:

1. **Never absorb or delete silently.** It's the host's own artifact, possibly still in
   active use by the IDE's UI — surface it and ask first, every time.
2. **Ask whether to absorb it, and route by shape.** If yes:
   - **A structured plan** (ordered steps, acceptance criteria, milestones) → create
     `memory/plans/<YYYY-MM-DD>-<slug>.md`, prepend the standard plan header
     (`core.planning.sk` `PLAN_WRITE` step 6: `Branch`, `Created`, `Status`, `Task file:`),
     and move the host file's plan content in with its structure intact — `## Steps` as a
     `[ ]` checklist, not a flattened paragraph. If the host file is itself epic-shaped
     (several independently-shippable pieces, each with its own criteria), add `Type: epic`
     and lay it out as `## Story` sections per that same step 6. Add the `Active plan:`
     pointer line to the task file. This preserves what a flatten-into-notes absorb would
     lose.
   - **Loose notes / scratch** (no real plan structure) → append to the current task file
     under a labeled heading (`## Absorbed from <filename> (<date>)`), dropping IDE-template
     boilerplate. Unchanged from before.
3. **Ask separately whether to delete the original.** Absorbing and deleting are two
   different confirmations — a user may want the content copied but the file left alone
   (e.g. the IDE's own panel still displays it).
4. **Then continue the normal boot sequence** — this doesn't gate task-file creation, it's
   a side note once the task file is already loaded/created.

---

## Why Task Memory Isn't Semantic Memory

Task memory is deliberately unscrutinized — the entire point of routing working notes
there instead of `project_knowledge.md` is so an agent can write down half-formed ideas,
dead ends, and in-progress reasoning without every line being held to the same bar as
permanent project truth. That means the *promotion* step (§TASK_CLOSE steps 2/2a) is the
only place that bar gets enforced. Skipping it — promoting everything in a task file
indiscriminately — defeats the reason the two tiers exist.

## Common Mistakes

1. **Treating task-memory closure as a formality.** Rubber-stamping everything in a task
   file into semantic memory is exactly how unverified, buggy, or rejected ideas become
   permanent "truths" that later sessions build on without question. Factually accurate
   (step 2) is not the same as accepted/correct (step 2a) — a description of a bug that's
   still in the code is a true statement and a terrible thing to promote.
2. **Deleting on a stale view.** Applying the Forgetting Policy without checking whether
   another branch added the thing you're about to delete.
3. **Letting archives grow forever.** `archived_tasks/` and `decisions.jsonl` both need an
   active pruning step, not just a place to write to.
4. **Assuming main/protected branches don't need task memory.** Trunk-based workflows and
   direct hotfixes are real; "no ticket branch" doesn't mean "no working notes," it means
   the notes need a rolling file that gets drained by `MEMORY_CONSOLIDATE` instead of an
   explicit `TASK_CLOSE`. Skipping task memory there and writing straight to
   `project_knowledge.md` is exactly the unverified-promotion failure mode this skill exists
   to prevent — it doesn't stop applying just because there's no branch name to point at.
5. **Fixing the bug but not the memory.** A bug traced back to a `knowledge/*.md` entry
   isn't fully fixed by patching the code — the entry that recommended the bad pattern is
   still sitting there as trusted ground truth for the next session and the next developer.
   Run `MEMORY_AMEND`, don't just quietly edit the file or leave it as-is.
