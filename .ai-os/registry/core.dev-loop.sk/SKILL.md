---
name: dev-loop
description: >-
  Implementation with independent peer review. Dispatches a separate reviewer
  when the host genuinely supports spawning subagents; falls back to a
  structured same-agent self-review, honestly labeled, when it doesn't.
  Never claims independent review happened on a host that can't do it.
---

# Dev Loop — Implementation with Peer Review

## Overview

A single agent that both writes code and assesses its own work has a structural blind
spot: it's grading its own reasoning. This skill adds a second, independent check —
*where the host genuinely supports it*.

The check is not conformance-only. Alongside correctness, conventions, security, and test
coverage, the Review Pass applies an **ownership-fit** lens: would the owner of this repo
merge this diff as-is, or is it in the wrong place / at the wrong abstraction / under-designed
even though it works? That is distinct from `core.simplicity.sk`, which is scoped to
over-engineering only.

**Realism constraint (read this before invoking):** spawning an independent subagent is a
host tool capability, not something every agentic AI can do — some hosts (Claude Code's
`Agent`/`Task` tool, or an equivalent) support it, many don't. This skill checks for that
capability at the start of every invocation and takes an honestly-labeled fallback path
when it's absent. It never claims a second, independent agent reviewed the work unless one
actually did — that would be exactly the kind of overclaim `core.self-healing.sk`'s
Response Credibility Protocol exists to catch.

## Dependencies

- `core.security.sk` — security review is part of what any review pass checks
- `core.self-healing.sk` — Verification-Before-Completion Protocol gates the final report
- `core.observability.sk` — logging which path was used and why
- `core.planning.sk` (optional) — consumes a `PLAN_WRITE` plan as the task spec when one
  exists for the current work

## Commands

### DEV_IMPLEMENT_REVIEWED

Implement a task with a review pass — independent when possible, self-review when not.

```
> OS_COMMAND DEV_IMPLEMENT_REVIEWED --task="<description>"
```

**Procedure:**

1. **Capability check.** Does the current host expose a genuine subagent-dispatch tool
   (e.g. an `Agent`/`Task`-style tool actually present in this session's tool list)? This
   is a real introspection check — confirm the tool is actually available this session,
   don't assume based on host name alone. Available → Path A. Not available → Path B.

2. **Path A — two-stage subagent review** (host supports subagent dispatch):
   a. Dispatch an implementer subagent with the task description, the approved plan from
      `PLAN_WRITE` if one exists for this task, and relevant conventions from
      `memory/semantic/knowledge/conventions_patterns.md`.

      **A subagent does not inherit this session's boot state.** Session-start context is
      parent-thread only — on Claude Code, `SessionStart` and `SubagentStart` are separate
      hook events, so `scripts/session-start-hook.sh` (EP-56) injects BOOT.md into this
      thread and into no dispatched agent. A subagent spawned without governance context is
      an ungoverned writer: no R1 pre-mutation security review, no R21 claim verification,
      no `AIOS-DEBT:` marker convention, no decision logging — and its output arrives here
      looking exactly like governed work. Every dispatch prompt therefore carries, inline:
      the Rules Digest (BOOT.md §3), the decision-log schema (§9), and the conventions
      above. Cost is real (repeated per dispatch) and is the price of the check being worth
      anything.

      On Claude Code specifically, EP-60 automates this: a `SubagentStart` hook entry runs
      `scripts/session-start-hook.sh SubagentStart`, injecting BOOT.md and `ultimate_rules.md`
      into every dispatched agent. **Verify it before relying on it** — the hook lives in the
      user's `.claude/settings.json`, not in this repo's payload, so it may be absent,
      matcher-narrowed to exclude the agent type being dispatched, or the host may not be
      Claude Code at all. Not confirmed present and in scope for this dispatch → carry the
      context inline as above. Never assume the hook fired.
   b. Once implementation returns, run the **Review Pass** (below) with the implementer's
      diff / changed files and the original task description as the spec. It is already on
      Path A's independent branch — a second, independent reviewer subagent.

3. **Path B — same-agent structured fallback** (no subagent capability):
   a. Implement the task normally.
   b. Run the **Review Pass** (below) against the diff you just produced. With no subagent
      tool it takes the fallback branch — an explicitly-labeled cold self-review.

4. Either path ends with `core.self-healing.sk`'s Verification-Before-Completion Protocol
   before reporting the task done.
5. Log which path was used and why in `memory/episodic/decisions.jsonl`.

---

### Review Pass

The second-opinion half of `DEV_IMPLEMENT_REVIEWED`, factored out so a skill that has
**already done its own implementation** can get the review without the implementer
dispatch. `core.planning.sk`'s `PLAN_EXECUTE` invokes this directly — once per flat plan
at completion, once per epic story at the story-done gate (EP-67). `DEV_IMPLEMENT_REVIEWED`
steps 2b / 3b are this same procedure.

Not a standalone `OS_COMMAND` — no independent invocation, always a step of a calling
command, so it emits no `▸ AI-OS` banner of its own (the caller already announced). The
caller emits one plain line naming the branch taken (`independent reviewer` /
`self-review fallback`) so the check is visible.

**Inputs:** the diff / changed file set, and the task spec — a plan's `## Context`, a
story's title + `### Acceptance Criteria`, or the original task description. **Never** the
implementer's reasoning or self-assessment (feeding the reviewer the implementer's
justification biases it toward agreement instead of independent judgment).

**Procedure:**
1. **Capability check** — same introspection as `DEV_IMPLEMENT_REVIEWED` step 1: is a
   genuine subagent-dispatch tool actually present this session? Available → step 2. Not →
   step 3. (A caller already on Path B has established there is none; the check just
   confirms it.)
2. **Independent branch** — dispatch one reviewer subagent with the diff + spec only.
   Carry governance context inline (Rules Digest, decision-log schema, conventions) unless
   the `SubagentStart` hook is confirmed present and in scope (step 2a's rule). Ask it to
   check the **Review checklist** (below).
3. **Fallback branch** — re-read the diff cold, as a **separate step** from any writing,
   against the same **Review checklist**. Report it plainly as a same-agent review, never
   worded as if a second agent checked the work.
4. Surface findings to the user as-is, including any disagreement with the implementation
   — do **not** auto-resolve by picking a side, and do **not** treat the pass as a
   completion gate. The caller decides what to act on.
5. Log which branch ran in `decisions.jsonl` (folded into the caller's own logging when it
   already logs a completion entry).

**Review checklist** — both branches (step 2 / step 3) check the same five:
- **Correctness** against the spec.
- **Convention adherence** — `memory/semantic/knowledge/conventions_patterns.md` + the
  surrounding code's idiom.
- **Security** — `SECURITY_SCAN_FILE`.
- **Test coverage** — the non-trivial logic has a check that fails if it breaks.
- **Ownership fit** — if you owned this repo, would you merge this diff in review without
  asking for changes? Is the code in the right module, at the right layer, behind the right
  seam, at an abstraction that matches the codebase's grain — not merely working,
  conventional, and secure? "Works but wrong home / wrong shape / under-designed" is a
  finding. This is *not* `core.simplicity.sk`'s scope (over-engineering only) — ownership
  fit also catches too little design, misplacement, and a leaky or mis-levelled seam.

---

## Common Mistakes

1. **Claiming independent review on a host without subagent capability** — the single
   most important failure mode this skill is built to prevent. If Path B ran, say Path B
   ran.
2. **Feeding the reviewer subagent the implementer's own reasoning trace** — biases the
   review toward rubber-stamping instead of judging the diff on its own merits.
3. **Auto-resolving reviewer disagreements** — surface them to the user; don't have the
   orchestrating agent unilaterally decide who was right.
4. **Dispatching a subagent without governance context** — it inherits none of this
   session's boot state (step 2a). Work comes back looking governed while having skipped
   R1, R21, and R13 entirely.
5. **Collapsing ownership fit into `core.simplicity.sk`'s scope** — the two are
   complementary, not the same. Simplicity flags *too much* (dead flexibility, one-caller
   layers, hand-rolled stdlib); ownership fit flags *wrong shape* in either direction —
   under-design, wrong module, wrong layer, an abstraction that fights the codebase's
   grain. A diff can be lean and still be in the wrong place.
