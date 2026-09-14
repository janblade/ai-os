# Operational Playbooks

> Pre-built response playbooks for common operational situations.
> These are starting templates — the agent refines them based on project-specific experience.

> A playbook specific to *this repo's own* dev process (not meant for any project that
> installs the framework) is marked `**Project-only**` on the line directly under its
> `## Playbook:` heading. `INSTALL_PROMPT.md` Step 4 strips any such section on fresh
> install — same treatment `RELEASE`/`EVOLVE_BENCHMARK` already get as commands (EP-75).

---

## Playbook: New Feature Development

### When to Use
User requests a new feature, capability, or component inside an existing project.

### Steps
1. **Clarify**: Run `PLAN_BRAINSTORM` to nail down acceptance criteria, edge cases, and
   what's explicitly out of scope — skip only for genuinely trivial, single-file work
   (use `DEV_IMPLEMENT_REVIEWED` directly for those; `BOOT.md` §4 routes plan-less feature
   requests there automatically).
2. **Plan**: Run `PLAN_WRITE` to turn the clarified feature into a concrete, ordered plan
   (or an epic with `## Story` sections, if it splits into independently shippable
   pieces). Present it and wait for approval before executing.
3. **Execute**: Run `PLAN_EXECUTE` — one step at a time. Before writing each step's code,
   apply `core.simplicity.sk`'s Simplicity Ladder (stop at the first rung that holds);
   verify each step (its named test/check) before moving to the next.
4. **Review**: No separate step needed — `PLAN_EXECUTE` runs `core.dev-loop.sk`'s Review
   Pass automatically (once per flat plan at completion, once per epic story at its
   story-done gate): correctness, convention adherence, security, test coverage, and
   ownership fit, surfaced as findings, non-blocking.
5. **Document**: If architectural insights were gained, update the relevant
   `memory/semantic/knowledge/*.md` sub-file — never overwrite `project_knowledge.md`
   directly, it's an index, not content.
6. **Close**: Run `TASK_CLOSE` when the feature is done and ready to hand off — it
   verifies each claim before promoting anything to semantic memory.

---

## Playbook: Bug Fix

### When to Use
User reports a bug, error, or unexpected behavior.

### Steps
1. **Reproduce**: Understand the exact failure condition.
2. **Check for a known fix**: Run `HEAL_DIAGNOSE` — its first step checks this file for a
   playbook matching the symptom before diagnosing from scratch. A match short-circuits
   straight to applying it.
3. **Diagnose**: No match → check `git diff` for the session's own recent mutations
   first (regressions are usually the most recent change), then trace the code for the
   root cause.
4. **Root Cause**: Identify the root cause, not just the symptom (R24). If it traces to a
   `knowledge/*.md` entry that's wrong or true-but-harmful, run `MEMORY_AMEND` too — a
   code fix alone leaves the entry trusted elsewhere.
5. **Fix**: Implement the minimal correct fix, applying the Simplicity Ladder.
6. **Test**: Write a regression test that would have caught the bug (`TEST_GENERATE` /
   `TEST_RUN`); use `TEST_IMPACT` to scope which other tests are actually affected.
7. **Verify**: Run the Verification-Before-Completion Protocol before reporting the fix
   done — "I read the diff and it looks right" doesn't count.
8. **Document**: If this took genuine diagnosis (not an obvious one-liner), offer to save
   it as a new `## Playbook:` entry here, same shape as this one, so `HEAL_DIAGNOSE` can
   find it next time.
9. **Log**: Record as a decision with the root cause analysis (R13).

---

## Playbook: Dependency Update

### When to Use
Updating, adding, or removing project dependencies.

### Steps
1. **Assess**: Why is this change needed? (Security patch, new feature, performance?)
2. **Check**: Run `SECURITY_CHECK_DEPS` on the new/updated dependency.
3. **Verify**: Check for breaking changes in changelogs.
4. **Update**: Apply the change with a lock file update (R18).
5. **Test**: Run `TEST_RUN`, or `TEST_IMPACT` first if scoping which tests the change
   actually affects.
6. **Log**: Record the dependency change decision.

---

## Playbook: Incident Response

### When to Use
Something has gone wrong in production or a critical failure has occurred.

### Steps
1. **Assess Severity**: Is this data loss, security breach, service outage, or degraded performance?
2. **Contain**: If security breach → `SECURITY_LOCKDOWN`. If service outage → identify affected systems.
3. **Diagnose**: Trace the failure. Check recent changes via `git diff` and `decisions.jsonl`.
4. **Fix or Rollback**: Apply a fix if clear and low-risk, otherwise `HEAL_ROLLBACK` to
   the last known good state.
5. **Verify**: Confirm the fix/rollback actually resolved the issue — Verification-
   Before-Completion Protocol, not just "should be fine now."
6. **Post-Mortem**: Document: what happened, why, how it was fixed, how to prevent recurrence.
7. **Harden**: Update tests, monitoring, or rules to prevent recurrence; if this class of
   incident could recur, save the response as a new playbook entry here.

---

## Playbook: Project Onboarding (New Contributor/Agent)

### When to Use
First boot on an existing project, or onboarding a new team member.

### Steps
1. **Scan**: Execute full perception scan (`INFRA_DETECT_STACK`).
2. **Read**: Load `project_knowledge.md` — it's an index; follow its links into
   `memory/semantic/knowledge/*.md` for the actual architecture, conventions, and gotchas.
3. **Map**: Review directory structure, entry points, and architecture.
4. **Verify**: Run `INFRA_HEALTH_CHECK` to confirm the project builds and tests pass.
5. **Summarize**: Add any new findings to the relevant `knowledge/*.md` sub-file — never
   raw notes back into `project_knowledge.md` itself.

---

## Playbook: Self-Evolution

### When to Use
The agent identifies a way to improve its own skills, commands, or workflows.

### Steps
1. **Identify**: What's the improvement? (New skill, better pattern, optimized workflow?)
2. **Propose**: Run `EVOLVE_PROPOSE` — writes the proposal to `progress.md` in
   `evolution_policy.md`'s PDCA format.
3. **Check Rules**: Confirm it doesn't violate any governance rule, and doesn't touch
   kernel space without an explicit `KERNEL OVERRIDE AUTHORIZED: {file}` from the user.
4. **Apply**: Low-risk, non-security → proceeds straight to `EVOLVE_APPLY`. Medium/high
   risk → present the proposal and wait for explicit approval first.
5. **Verify**: Run an integrity check; if a skill was modified, dry-test it.
6. **Log**: Record in `decisions.jsonl` and update the proposal's `Status` in `progress.md`.
7. **Release**: In this repo (MaiKS's own dev repo), finish with `RELEASE` — one commit
   per applied EP, pushed to `main`. An installed project follows its own VCS conventions
   instead; `RELEASE` isn't shipped to installs.

---

*These playbooks are living documents. The agent refines them based on project-specific experience.*
