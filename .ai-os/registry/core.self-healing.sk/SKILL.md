---
name: self-healing
description: >-
  Circuit breakers, loop detection, failure classification, auto-repair, and
  emergency protocols. Makes the AI OS resilient to failures — it detects when
  something is broken and repairs itself or escalates gracefully.
---

# Self-Healing & Resilience

## Overview

Production AI systems fail. The self-healing skill ensures failures are detected,
classified, and recovered from — automatically when possible, with human escalation
when necessary. It implements loop detection and failure classification from BOOT.md §7.

Note: there is no live per-skill circuit-breaker *state* maintained anywhere (an agent
can't reliably keep persistent counters up to date across sessions). "Circuit status"
below is computed on demand from the failure/repair pattern visible in `decisions.jsonl`,
not read from a stored flag.

## Dependencies

- `observability.sk` — Required for logging diagnoses and repairs

## Commands

### HEAL_DIAGNOSE

Diagnose system issues.

```
> OS_COMMAND HEAL_DIAGNOSE [--scope=framework|project|all] [--auto-repair]
```

**Procedure:**
1. **Check for a known fix.** Read `memory/procedural/playbooks.md` and scan playbook
   titles and `### When to Use` lines for one matching this failure's symptom (error
   message, stack trace, or failing command). Match → follow its `### Steps` directly,
   tell the user which playbook matched and why, then skip to step 4. No match → continue.
2. **Framework Diagnosis:** Review `ultimate_rules.md` and `BOOT.md` to ensure you haven't violated any governance constraints.
3. **Project Diagnosis:** check `git diff` for recent mutations first (R24). If that
   doesn't show the cause, run the Reproduce-First Diagnosis Loop below — no theory about
   the cause before its phase 1 exit condition holds.
4. **Report Findings:** Clearly explain the root cause of the failure to the user before
   attempting a fix, with its R24 confidence (High needs the loop's red command to have
   reproduced it).

---

### HEAL_REPAIR

Auto-repair detected issues.

```
> OS_COMMAND HEAL_REPAIR [--issue=<id>] [--all-safe]
```

**Repair strategies by issue type:**

| Issue | Repair Strategy |
|---|---|
| Missing user-space file | Recreate from default template |
| Orphaned skill registration | Remove from `index.json` |
| Missing skill registration | Add to `index.json` based on disk scan |
| Corrupt JSON file | Attempt parse recovery; if impossible, reset to default |
| Corrupt JSONL file | Remove malformed lines, preserve valid entries |
| Stale project genome | Re-run perception scan |
| Orphaned evolution proposal | Mark as EXPIRED |

**Safety rules:**
- NEVER repair kernel-space files without human approval
- NEVER delete memory without logging what was removed
- NEVER modify security.sk during repair
- Always log every repair action in `decisions.jsonl`

If `--all-safe`: Repair all issues that are safe to auto-fix (LOW + MEDIUM severity).

---

### HEAL_ROLLBACK

Rollback to last known good state.

```
> OS_COMMAND HEAL_ROLLBACK [--scope=last-evolution|last-session|full-reset]
```

**Scopes:**
- `last-evolution`: Revert the most recent evolution (delegates to `EVOLVE_ROLLBACK`)
- `last-session`: Revert all changes made in the current session (requires session tracking)
- `full-reset`: Reset all user-space files to default templates (DESTRUCTIVE — requires confirmation)

**Procedure:**
1. Identify the rollback scope
2. For `last-evolution`: Use preserved state from evolution skill
3. For `last-session`: Use git diff or session change log to identify and revert changes
4. For `full-reset`: Confirm with user, then recreate all user-space files from defaults
5. Run integrity check after rollback
6. Log rollback in `decisions.jsonl`

---

### HEAL_CIRCUIT_STATUS

Report which skills look degraded, based on recent logged failures — not a stored flag.

```
> OS_COMMAND HEAL_CIRCUIT_STATUS
```

**Procedure:**
1. Read the recent tail of `decisions.jsonl` (last ~50 entries is plenty).
2. Group `type: "action"` entries that describe a failed operation or a repair by which
   skill/command they relate to.
3. A skill is **degraded** if 3+ of its recent operations failed with no successful repair
   logged afterward; otherwise **healthy**.
4. Report a short table: skill, recent failure count, status. This is a heuristic read of
   the log, not a certified live state — say so if asked.

---

### REVIEW_CREDIBILITY

Structured credibility audit of the framework and project documentation.

```
> OS_COMMAND REVIEW_CREDIBILITY [--scope=framework|project|all] [--fix]
```

**Scopes:**
- `framework`: Audit only `.ai-os/` files (BOOT.md, rules, skills, registry, memory, installer)
- `project`: Audit project-facing files (README.md, docs, API documentation)
- `all` (default): Audit everything

**Procedure:**
1. **Read every file** in scope. Do not skim — read the full contents of each file.
2. **Run the following checks** against each file, categorizing findings as CRITICAL / MEDIUM / LOW:

| Check | Category | What to Look For |
|---|---|---|
| **Overclaims** | CRITICAL | Compliance claims without certification (e.g., "ISO certified"), unverifiable performance guarantees (e.g., "near-zero latency"), marketing superlatives presented as facts |
| **Internal Inconsistencies** | CRITICAL | File paths in documentation that don't match actual disk structure, naming mismatches between registries (e.g., `commands/index.json` referencing skills without correct namespace prefix) |
| **Unimplemented Features** | CRITICAL | Systems that are defined/documented but never loaded, enforced, or connected (e.g., config files that nothing reads, feature flags with no toggle mechanism) |
| **Contradictions** | MEDIUM | Files that criticize a pattern then implement that exact pattern, rules that claim to be enforced but have no enforcement mechanism |
| **Buzzword Inflation** | MEDIUM | Excessive use of trendy prefixes ("cognitive", "AI-native", "intelligent") where plain language would be more credible, especially in technical documentation aimed at engineers |
| **Data Accuracy** | LOW | Command counts, version numbers, timestamps, or statistics that don't match the actual state of the system |

3. **Cross-reference registries**: Verify that `commands/index.json`, `registry/index.json`, and `kernel/integrity.md` all agree on file paths, skill names, and command lists.
4. **Verify all claims are supportable**: For every claim in the README or documentation, ask: "Could a skeptical senior engineer verify this?" If not, flag it.
5. **Generate a structured report** organized by severity tier (CRITICAL → MEDIUM → LOW) with:
   - The specific file and line where the issue was found
   - What's wrong and why it damages credibility
   - A concrete fix suggestion with estimated effort
6. **If `--fix` is specified**: After presenting the report, proceed to fix all issues automatically (CRITICAL first, then MEDIUM, then LOW). Commit with a descriptive message.
7. **Log the review** in `memory/episodic/decisions.jsonl`.

**When to run this:**
- Before open-sourcing a project
- Before presenting the framework to a team or stakeholders
- After a large batch of structural changes (like adding new skills or rewriting docs)
- Periodically as part of framework hygiene (recommended: once per major version)

---

## Response Credibility Protocol

Before presenting any substantive response (architecture proposals, code suggestions,
technical recommendations, evolution proposals, diagnostic conclusions), apply this
mental checklist. This is NOT a command — it is a behavioral protocol.

### Checklist (apply silently — do not print this to the user)

1. **Claim Verification**: Does my response contain factual claims? Can I trace each
   claim to a file I've read, a command I've run, or established knowledge? If not,
   qualify it: "I believe..." or "Based on common patterns..." instead of stating
   as fact.

2. **Overclaim Detection**: Am I promising outcomes I can't guarantee? Watch for:
   - "This will fix..." → prefer "This should fix..." or "This addresses the likely cause..."
   - "This is the best..." → prefer "This is a strong option because..."
   - "This is production-ready..." → prefer "This handles [specific cases]; you should also test [edge cases]"
   - Absolute guarantees about security, performance, or correctness

3. **Scope Honesty**: Am I suggesting something beyond what I've actually verified?
   - If I haven't read a file, I should not claim to know its contents
   - If I haven't run a test, I should not claim code works
   - If I haven't checked dependencies, I should not claim compatibility

4. **Alternative Acknowledgment**: For significant technical decisions, have I
   mentioned at least one alternative approach and why I'm not recommending it?
   (Per Rule R8 — Alternatives Considered)

5. **Limitation Disclosure**: Am I being transparent about what I don't know or
   haven't checked? Credibility comes from honesty about boundaries, not from
   projecting omniscience.

6. **Confidence Calibration**: Is my language calibrated to my actual confidence?
   - **High confidence** (read the code, ran the test, verified): Direct statements
   - **Medium confidence** (pattern-matched, inferred from context): Qualified statements
   - **Low confidence** (educated guess, no direct evidence): Explicit uncertainty markers

7. **Sycophancy Resistance** (R25): Am I shading this toward what the user wants to
   hear rather than what's true? A technically-accurate answer that emphasizes only
   positives, buries a real weakness under caveats, or softens a blunt conclusion into
   vagueness fails this even with zero false claims. Lead with the direct assessment.

### What This Does NOT Mean

- ❌ Do NOT add verbose disclaimers to every response
- ❌ Do NOT hedge simple factual statements ("the file is at path X")
- ❌ Do NOT slow down trivial operations with unnecessary self-doubt
- ✅ DO calibrate language to confidence level on substantive claims
- ✅ DO admit when you haven't verified something
- ✅ DO mention alternatives for significant decisions

---

## Verification-Before-Completion Protocol

The Response Credibility Protocol above governs how a claim is *worded*. This protocol
governs whether the claim was *earned* — the action taken immediately before reporting any
task, feature, or fix as complete. A well-hedged but unverified "this should work" still
fails this gate even though it would pass the credibility checklist.

### Before reporting anything done

1. **Run what can be run.** Existing test suite, build, lint/typecheck for the changed
   area — via `TEST_RUN`/`TEST_IMPACT` (`core.testing.sk`) or the project's own build
   command. "I read the diff and it looks right" is not verification.
2. **Exercise the golden path for user-facing changes.** UI/CLI/API-surface changes need
   to actually be invoked once with realistic input, not just type-checked.
3. **Check for leftovers.** No stray debug output, no TODO/stub left where a real
   implementation was expected, no commented-out old version of the code.
4. **Nothing to run** (pure documentation, config comment, non-executable content) → say
   so explicitly ("no automated check applies here — verified by reading") rather than
   silently skipping the gate. The absence of a check is itself something to disclose,
   not something to leave implicit.

### Failure handling

If verification fails or can't be completed (no test framework detected, build tool
unavailable, etc.), report the task as **not yet verified**, not as done — and say what
specifically wasn't checked. Don't downgrade this to a caveat buried after a "completed"
headline.

---

## Reproduce-First Diagnosis Loop

The procedure behind R24 when the diff doesn't show the cause. The failure it prevents:
read code, guess a cause, patch it, and call the symptom gone. Each phase has an exit
condition you can check; don't move on until it holds.

1. **Red command first.** Build one command that drives the real code path and asserts the
   user's exact symptom — a test, an HTTP/CLI script, a fixture diff, a replayed payload —
   and run it once and watch it fail. *Exit:* it exists and is red for the reported reason.
   No hypothesis before this. Can't build one → say what you tried and ask for access, logs,
   or a captured artifact; don't proceed on a guess.
2. **Confirm and shrink.** Check the failure is the reported one, not a nearby one (same
   error, same place, same input class). Cut inputs and steps until removing anything more
   turns it green. Flaky → raise the reproduction rate (loop it, pin the seed, fix the
   clock) before going on. *Exit:* a minimal case that fails every run, or a stated rate.
3. **Ranked, falsifiable hypotheses.** Write 3-5 candidate causes, most likely first, each
   with the observation that would *disprove* it. This is what R24's High/Medium/Low gate
   grades. *Exit:* the list exists before any instrumentation.
4. **One variable at a time.** Test the top hypothesis with the smallest probe that can
   falsify it. Debug output carries one unique tag (e.g. `DBG-<short-id>`) so cleanup is a
   single grep. Disproved → next hypothesis; all disproved → back to phase 3 with what you
   learned; a second full round with nothing surviving → stop and escalate, as Loop
   Detection below does for repeated fixes. *Exit:* one hypothesis
   survives and the others are ruled out by evidence, not preference.
5. **Regression test before the fix**, at a seam that exercises the real bug (the red
   command often becomes it). It must fail now. No such seam → report that as a finding;
   don't write a shallow test that passes either way (`core.testing.sk` anti-patterns).
6. **Fix, then cleanup gate.** Minimal fix (Simplicity Ladder). Done only when the tag
   greps to zero, the red command and regression test pass, and `TEST_IMPACT`'s scope is
   green — then the Verification-Before-Completion Protocol below.

Scale it to the bug: an obvious one-liner whose diff already shows the cause skips to
phase 5. Phase 1 is never skipped when the cause isn't already known.

---

## Loop Detection

If you find yourself attempting the same fix 3 times and receiving the same error, **STOP**.
Do not blindly retry a 4th time. Escalate to the user and ask for guidance or alternative approaches.

## Repair Protocol

When you encounter a persistent failure:
1. **Check `memory/procedural/playbooks.md` first** — this loop-triggering failure may be
   one it already has the answer to (same check as `HEAL_DIAGNOSE` step 1, restated here
   because this protocol also fires ambiently on loop detection, not only via an explicit
   `HEAL_DIAGNOSE` invocation). Match → follow its `### Steps`, tell the user which
   playbook matched, skip the rest of this protocol. No match → continue.
2. Stop the current action chain.
3. Formulate a new hypothesis. If the local fix isn't working, consider if the root cause is in a different file or dependency.
4. Use your file reading tools (`view_file`, `grep_search`) to gather broader context.
5. Attempt an alternative strategy.
6. **If the repair is successful**, ask the user: *"I have successfully repaired the
   issue. Would you like me to document this fix in `playbooks.md` so `HEAL_DIAGNOSE` can
   find it automatically next time?"* On yes, append a new `## Playbook: <short
   descriptive name>` section in the same shape as the file's existing entries —
   `### When to Use` (the symptom/error signature this matches) and `### Steps` (the
   working fix, generalized past this one file/instance) — not free-form notes, so step 1
   above can actually match against it later.

## Common Mistakes

1. **Blind Retries** — Retrying the exact same command hoping it will work.
2. **Ignoring Root Causes** — Fixing the symptom instead of the underlying architectural flaw.
3. **Not Logging Repairs** — Every repair is a learning opportunity. Always log what was broken and how it was fixed.
4. **Re-diagnosing a failure `playbooks.md` already has a fix for** — check it first
   (`HEAL_DIAGNOSE` step 1 / Repair Protocol step 1) before spending a fresh diagnosis pass
   on a problem already solved once. A playbook that never gets checked is why the
   diagnosis effort repeats forever instead of only once (EP-72).
5. **Writing a playbook entry as free-form notes** — an undocumented shape can't be
   matched against later. New entries from the Repair Protocol follow the existing
   `## Playbook:` / `### When to Use` / `### Steps` structure, not prose.
