---
name: simplicity
description: >-
  Complexity governance. A pre-mutation simplicity ladder that runs before code
  is written, a marker convention for deliberate shortcuts, and review/audit
  passes scoped strictly to over-engineering — what to delete, what the stdlib
  or platform already ships, what abstraction has one caller.
---

# Simplicity — Complexity Governance

## Overview

R1 gates every code mutation on security. Nothing gates it on necessity. The result is the
most common agentic-coding output defect after a wrong fix: code that works, passes review,
and should not exist — a wrapper that only delegates, an interface with one implementation,
a hand-rolled function the standard library already ships.

R22 (Scope Discipline) is the nearest existing rule but is narrower and ADVISORY: it forbids
*bundling* unrequested refactors into a task. It says nothing about the requested work itself
being over-built. This skill covers that gap.

Adapted from `DietrichGebert/ponytail` (MIT) — the ladder, the finding-tag taxonomy, the
deliberate-shortcut marker, and the no-invented-baseline honesty rule. Deliberately dropped:
its persistent lite/full/ultra session mode, which is enforced by a hook-written flag file
this framework has no equivalent of. A mode this framework claimed to "keep active every
response" would be unenforceable self-report — the exact overclaim class
`core.self-healing.sk`'s Response Credibility Protocol exists to catch. Intensity here is a
per-invocation parameter with an archetype-derived default instead.

## Dependencies

- `core.security.sk` — R1's pre-mutation review still runs first; the ladder never precedes it
- `core.testing.sk` — a simplification's proof is its check (see Non-Negotiables)
- `core.self-healing.sk` — Response Credibility Protocol governs how findings are worded
- `core.observability.sk` — logging accepted/rejected simplifications

---

## The Simplicity Ladder

Runs after R1's security review, before writing code. Stop at the first rung that holds:

1. **Does this need to exist at all?** Speculative need → skip it, say so in one line (YAGNI).
2. **Already in this codebase?** Existing helper/util/type/pattern → reuse it. Check
   `memory/semantic/knowledge/conventions_patterns.md` and grep before writing. Re-implementing
   what already lives two files over is the single most common form of this defect.
3. **Standard library does it?** Use it.
4. **Native platform feature covers it?** DB constraint over app code, CSS over JS,
   `<input type="date">` over a picker dependency.
5. **Already-installed dependency solves it?** Use it. Never add a new dependency for what a
   few lines cover — a new dependency is also an R1 + `SECURITY_CHECK_DEPS` event, not a
   free choice.
6. **Can it be one line?** One line.
7. **Only then:** the minimum code that works.

**The ladder shortens the solution, never the reading.** It runs *after* the problem is
understood — task read, affected code traced end to end — not instead of. A minimal diff in
the wrong place is not simplicity, it is a second bug wearing efficiency as a costume. This
is R24 (Root Cause Before Fix) stated from the other direction: the lazy fix and the
root-cause fix are usually the same fix, because one guard in the shared function is a
smaller diff than one guard in every caller — and patching only the path the report names
leaves every sibling caller broken.

Two rungs both hold → take the higher one and move on. Two options at the same rung and the
same size → take the one that is correct on edge cases. Less code, never the flimsier
algorithm.

### Intensity

Per-invocation, not a persistent mode. Default derives from
`manifest.json.project_archetype`; `--level` overrides for one invocation.

| Level | Behavior | Archetype default |
|---|---|---|
| `advisory` | Build what was asked; name the simpler alternative in one line, user decides | `enterprise`, `critical` |
| `standard` | Ladder enforced. Shortest correct diff, shortest explanation | `hobby`, `startup` |
| `aggressive` | Challenge the requirement itself before building; deletion before addition | never a default — opt-in only |

`aggressive` is never an archetype default: on `enterprise`/`critical` it collides with R15
(human approval for irreversible actions), and challenging a requirement unprompted is a
scope negotiation, not a code decision.

---

## Non-Negotiables

Never simplified away, at any level: input validation at trust boundaries, error handling
that prevents data loss, anything under `rules/security_policy.md`, accessibility basics,
logging that R13 requires, anything the user explicitly asked for. User restates the fuller
version after the alternative is named → build it, don't re-argue (R25 covers stating the
disagreement once, plainly; it does not license repeating it).

Real-world calibration is not complexity. Physical systems drift — a clock, a sensor, a rate
limiter under real load. A tuning knob a minimal model has no reason to include is a
requirement, not bloat.

**A simplification without its check is unfinished.** Non-trivial logic (a branch, a loop, a
parser, a money or auth path) leaves behind one runnable check — the smallest thing that
fails if the logic breaks. Full TDD discipline is `core.testing.sk`'s RED-GREEN-REFACTOR;
this is its floor, not a replacement. Trivial one-liners need no test — YAGNI applies to
tests too, and a test suite is code that can be over-built like any other.

---

## Deliberate-Shortcut Markers

A simplification that cuts a real corner with a known ceiling (global lock, O(n²) scan, naive
heuristic, in-memory store) is marked in the code at the point of the shortcut:

```
# AIOS-DEBT: <the ceiling>, <what triggers the upgrade>
# AIOS-DEBT: global lock, per-account locks if write throughput matters
// AIOS-DEBT: O(n^2) pair scan, index it above ~5k rows
```

Two fields, both required. A marker naming a ceiling but no trigger is how "later" becomes
"never" — `DEBT_LEDGER` flags those specifically.

Marker vs. memory: an `AIOS-DEBT:` marker records a *deliberate local shortcut whose fix
lives at that line*. A finding about the project's architecture or conventions still goes to
task memory and is promoted per §9. Don't route one through the other.

---

## Commands

### SIMPLIFY_REVIEW

Review a diff for over-engineering only.

```
> OS_COMMAND SIMPLIFY_REVIEW [--target=<diff|branch|files>] [--level=advisory|standard|aggressive]
```

**Procedure:**

1. Resolve the target — default `git diff` against the merge base of the current branch.
2. Read the changed code *and* what it calls into. A finding that ignores an existing caller
   is a wrong finding.
3. Emit one line per finding: `<file>:L<line>: <tag> <what to cut>. <replacement>.`
4. Close with the counted total (see Honesty Boundary). Nothing to cut → `Lean already.` and stop.

**Tags:**

| Tag | Meaning | Replacement field |
|---|---|---|
| `delete:` | Dead code, unused flexibility, speculative feature | nothing |
| `stdlib:` | Hand-rolled thing the standard library ships | name the function |
| `native:` | Code or dependency doing what the platform already does | name the feature |
| `yagni:` | Abstraction with one implementation, config nobody sets, layer with one caller | what to inline it into |
| `shrink:` | Same logic, fewer lines | the shorter form |
| `dup:` | Re-implements something already in this codebase | path to the existing one |

```
✅ src/mail.py:L12-38: stdlib: 27-line email validator class. "@" in address plus a confirmation mail; RFC-parsing it locally proves nothing.
✅ web/date.js:L4: native: moment.js imported for one format call. Intl.DateTimeFormat, 0 deps.
✅ store/repo.py:L88: yagni: AbstractRepository, one implementation. Inline until a second exists.
✅ api/client.go:L52-71: delete: retry wrapper around an idempotent local call. Nothing replaces it.
❌ "This validator class might be more complex than necessary — have you considered whether all of these rules are needed at this stage?"
```

The ❌ form is the failure mode this command exists to replace: a hedge with no location, no
cut, and no replacement, which costs tokens and decides nothing.

**Scope:** over-engineering only. Correctness bugs → `core.dev-loop.sk` / a normal review
pass. Security → `SECURITY_REVIEW_CHANGE`. Doc/claim accuracy → `REVIEW_CREDIBILITY`.
Reports findings; applies nothing. The one runnable check required by Non-Negotiables is the
floor, never a `delete:` finding.

### SIMPLIFY_AUDIT

`SIMPLIFY_REVIEW` across the whole tree instead of a diff.

```
> OS_COMMAND SIMPLIFY_AUDIT [--scope=<path>] [--level=advisory|standard|aggressive]
```

Same tags, same output line, ranked biggest cut first. Hunt list: dependencies the stdlib or
platform already ships, single-implementation interfaces, factories with one product,
wrappers that only delegate, modules exporting one thing, dead feature flags, config nobody
reads, hand-rolled stdlib.

R23 applies to acting on the results: a repo-wide audit surfaces wide-reaching changes by
construction. The audit itself is read-only; each accepted finding is its own change with its
own blast-radius assessment. Do not batch-apply an audit.

### DEBT_LEDGER

Harvest every `AIOS-DEBT:` marker into one ledger, so a deferral can't quietly become permanent.

```
> OS_COMMAND DEBT_LEDGER [--scope=<path>] [--write=<file>]
```

**Procedure:**

1. `grep -rnE '(#|//|--|;|/\*) ?AIOS-DEBT:' <scope>`, excluding VCS, dependency, and build
   directories **and `registry/core.simplicity.sk/`**. Requiring a comment prefix keeps
   prose that merely mentions the convention out of the ledger, but not this file's own
   fenced examples — those carry a real prefix and matched the scan on its first run, so
   the definition file is excluded by path.
2. One row per marker, grouped by file:
   `<file>:<line> — <what was simplified>. ceiling: <limit>. upgrade: <trigger>.`
3. Marker with no upgrade trigger → tag the row `no-trigger`. Those are the ones that rot.
4. Close with `<N> markers, <M> with no trigger.` None found → `No AIOS-DEBT markers.`
5. `--write` given → persist to that file. Without it, report only; never write unasked.

Owner per row → `git blame -L<line>,<line>` on the marker line.

---

## Honesty Boundary

`SIMPLIFY_REVIEW`/`SIMPLIFY_AUDIT` close with `net: -<N> lines possible`, where N is counted
from the actual lines proposed for deletion. That is the only number either command emits.

**Never report savings for code that was never written.** "This approach saved ~400 lines" /
"the ladder cut token cost by X%" have no measurable baseline — the unbuilt version does not
exist to subtract from. Under R21 that is an unverifiable assertion, and under R25 it is the
flattering shape of one. `DEBT_LEDGER`'s marker count and a review's counted deletion total
are real because both are counted off disk; a savings percentage against a hypothetical is not.

Findings inherit the Response Credibility Protocol. `stdlib:` names a function that exists in
this project's language version — verified this session, not recalled (R21). Unverified →
`shrink:` with the shorter form shown, or drop the finding. A confidently wrong `stdlib:`
finding costs more than the complexity it was flagging.

---

## Common Mistakes

1. **Climbing before reading.** The ladder runs on an understood problem. Skipping
   comprehension to reach a small diff produces a confident wrong fix — the failure mode R24
   and this skill's own ladder text both exist to prevent.
2. **Treating the ladder as a research project.** It is a reflex. Two rungs hold → take the
   higher one and move on. Deliberating the rungs costs more than the code being avoided.
3. **Prose defending a simplification.** If the explanation outruns the code, the explanation
   is the complexity. Explanation the user explicitly asked for is not debt — give it in full.
4. **Bundling audit findings into an unrelated task.** R22 is not suspended by this skill;
   it is the reason the review commands report and never apply.
5. **Inventing a savings figure.** See Honesty Boundary. The counted deletion total or nothing.
6. **Marking a shortcut with no upgrade trigger.** A ceiling without a trigger is an excuse
   with a comment prefix.
