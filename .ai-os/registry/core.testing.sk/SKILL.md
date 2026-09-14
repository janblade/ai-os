---
name: testing-validation
description: >-
  Test execution, coverage analysis, AI-assisted test generation, regression
  testing, and test impact analysis. Ensures code quality through comprehensive
  automated testing workflows.
---

# Testing & Validation

## Overview

The testing skill ensures code quality through automated testing. It runs existing
tests, generates new ones, analyzes coverage gaps, and determines which tests are
affected by code changes.

## Commands

### TEST_RUN

Execute test suites with structured output.

```
> OS_COMMAND TEST_RUN [--suite=<name>] [--filter=<pattern>] [--verbose]
```

**Procedure:**
1. Detect test framework from project genome (Jest, pytest, cargo test, go test, etc.)
2. Build the appropriate test command:
   | Framework | Command |
   |---|---|
   | Jest | `npx jest [--testPathPattern=<filter>]` |
   | Vitest | `npx vitest run [--reporter=verbose]` |
   | pytest | `python -m pytest [-k <filter>] [--tb=short]` |
   | cargo test | `cargo test [<filter>]` |
   | go test | `go test ./... [-run <filter>]` |
   | JUnit | `./gradlew test [--tests <filter>]` |
3. Execute and capture output
4. Parse results into structured format: total, passed, failed, skipped, duration
5. Log test results in `memory/episodic/decisions.jsonl` if failures detected

---

### TEST_COVERAGE

Generate and analyze coverage reports.

```
> OS_COMMAND TEST_COVERAGE [--threshold=<percent>]
```

**Procedure:**
1. Run tests with coverage enabled (framework-specific flags)
2. Parse coverage output for: line coverage, branch coverage, function coverage
3. Identify uncovered files and functions
4. If `--threshold` specified: Compare against threshold, report pass/fail
5. Generate summary: "Coverage: {percent}% — {uncovered_count} files below threshold"

---

### TEST_GENERATE

AI-assisted test generation for uncovered code.

```
> OS_COMMAND TEST_GENERATE --file=<path> [--style=unit|integration]
```

**Procedure:**
1. Read the target source file
2. Load testing patterns from `memory/semantic/patterns.json`
3. Identify untested functions, branches, and edge cases
4. Generate test file following project conventions:
   - Match existing test naming pattern
   - Match existing test structure (describe/it, test classes, etc.)
   - Include happy path, error cases, and boundary conditions
5. Run SECURITY_SCAN_FILE on generated tests
6. Present generated tests to user for review before writing

---

### TEST_REGRESSION

Run regression suite against recent changes.

```
> OS_COMMAND TEST_REGRESSION [--since=<commit|date>]
```

**Procedure:**
1. Identify files changed since the specified point (default: last session)
2. Use TEST_IMPACT to determine affected tests
3. Run only the affected tests
4. Compare results against previous run: new failures = regressions
5. Report: "Regression check: {result} — {new_failures} new failures detected"

---

### TEST_IMPACT

Test impact analysis — determine which tests need to run.

```
> OS_COMMAND TEST_IMPACT --changed=<file1,file2,...>
```

**Procedure:**
1. Parse changed files
2. Trace import/dependency chains to find which test files reference the changed code
3. Include tests that directly import changed modules
4. Include tests in the same directory/package as changed files
5. Include integration tests that exercise changed endpoints/functions
6. Report: "Impact analysis: {count} tests affected by changes to {files}"

---

## Test-Driven Development Discipline

When implementing a new feature or fixing a bug, follow RED → GREEN → REFACTOR rather than
writing the implementation first and backfilling tests afterward:

1. **RED** — Write a test for the behavior that doesn't exist yet. Run it
   (`TEST_RUN --filter=<new_test>`) and confirm it fails *for the expected reason*
   (missing implementation, not a typo or setup error). A test that passes before the
   code exists is testing nothing.
2. **GREEN** — Write the minimum code needed to make the test pass. Resist adding
   unrelated functionality at this step.
3. **REFACTOR** — With the passing test as a safety net, clean up the implementation
   (naming, duplication, structure). Re-run the test after each change; it must stay green.

Not every change needs a formal RED phase — trivial edits (typo fixes, config value
changes, doc updates) have no meaningful "failing test" to write first. Apply this to new
behavior and bugfixes, where skipping RED is how regressions get reintroduced silently.

### Anti-Patterns

1. **Test-after, labeled as TDD** — Writing the implementation first, then a test that
   exercises the code path you already know works. This verifies the code does what you
   wrote, not what was actually required — it can't catch "wrote the wrong thing."
2. **Asserting on implementation details** — Testing internal call order, private state, or
   mock-call counts instead of observable behavior/output. Breaks on refactors that don't
   change behavior, which trains people to ignore test failures.
3. **Disabling instead of fixing** — Skip-marking or deleting a failing test to unblock a
   commit, rather than fixing the regression or updating the test if the requirement
   genuinely changed. A silently skipped test is a false "all green."

---

## Common Mistakes

1. **Running all tests when only a few files changed** — Use TEST_IMPACT to scope test runs.
2. **Generating tests without reading patterns first** — Generated tests should match project conventions.
3. **Ignoring flaky tests** — If a test passes sometimes, it's not a passing test. Investigate.
