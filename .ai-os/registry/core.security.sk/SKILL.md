---
name: security-audit
description: >-
  Vulnerability scanning, dependency auditing, pre-commit security gates, and
  emergency lockdown. Enforces OWASP GenAI Top 10 defenses and ensures all code
  mutations pass security review before execution. This skill is PROTECTED —
  modifications require human approval regardless of archetype.
---

# Security Audit & Enforcement

## Overview

The security skill is the gatekeeper of the AI OS. No code enters or leaves the
project without a review. It implements the pre-mutation security checklist defined in
BOOT.md §6 and enforces the security policy from `rules/security_policy.md`.

> [!CAUTION]
> This skill is **PROTECTED**. Unlike other skills, modifications to `security.sk`
> require explicit human approval at ALL archetype levels. This prevents the agent
> from weakening its own security controls.

## Commands

### SECURITY_AUDIT

Full workspace vulnerability scan.

```
> OS_COMMAND SECURITY_AUDIT [--depth=quick|standard|all] [--scope=<path>]
```

**Parameters:**
- `--depth` (default: `standard`)
  - `quick`: Secrets scan only — fast, catches hardcoded credentials
  - `standard`: Secrets + injection patterns + unsafe functions
  - `all`: Full scan including dependency audit, license check, and configuration review
- `--scope` (default: `.`): Limit scan to a specific directory or file

**Procedure:**
1. Read all files in scope
2. Review for secret patterns: hardcoded API keys, AWS credentials, private keys, tokens, passwords
3. Review for injection vulnerabilities: command injection, SQL injection, XSS, path traversal
4. Review for unsafe function usage (`eval`, `exec`, `os.system`, `pickle.loads`, etc.)
5. If `--depth=all`: Run dependency vulnerability check (SECURITY_CHECK_DEPS)
6. Generate report: findings count by severity, file locations, recommended fixes
7. Log scan result in `memory/episodic/decisions.jsonl`

**Output:** Structured scan report with findings categorized as CRITICAL / HIGH / MEDIUM / LOW.

---

### SECURITY_SCAN_FILE

Scan a specific file for vulnerabilities.

```
> OS_COMMAND SECURITY_SCAN_FILE --file=<path>
```

**Procedure:**
1. Read the target file
2. Run all pattern checks (secrets, injection, unsafe functions)
3. Report findings or "CLEAN — no vulnerabilities detected"

This is the command invoked automatically by the pre-commit security gate.

---

### SECURITY_CHECK_DEPS

Dependency vulnerability check.

```
> OS_COMMAND SECURITY_CHECK_DEPS [--fix]
```

**Procedure:**
1. Identify the project's dependency files (package.json, pyproject.toml, Cargo.toml, etc.)
2. Parse installed dependencies and their versions
3. Cross-reference against known vulnerability patterns:
   - Deprecated packages
   - Packages with known CVEs
   - Suspiciously named packages (typosquatting detection)
   - Packages with no recent updates (>2 years)
4. Report findings with severity and recommended actions
5. If `--fix`: Suggest version upgrades for vulnerable packages

---

### SECURITY_REVIEW_CHANGE

Pre-commit security review of staged or proposed changes.

```
> OS_COMMAND SECURITY_REVIEW_CHANGE [--files=<file1,file2,...>]
```

**Procedure:**
1. Identify changed files (from git diff or explicit list)
2. Run SECURITY_SCAN_FILE on each changed file
3. Check for new dependencies added
4. Check for permission changes (file mode changes)
5. Check for new API endpoints or exposed surfaces
6. Generate change-specific security review

**This command is automatically invoked before any code mutation** per Rule R1.

---

### SECURITY_LOCKDOWN

Emergency freeze — halt all autonomous operations.

```
> OS_COMMAND SECURITY_LOCKDOWN [--reason=<description>]
```

**Procedure:**
1. Set all skill circuit breakers to OPEN
2. Disable autonomous operations
3. Log the lockdown event with timestamp and reason
4. Notify user immediately: "SECURITY LOCKDOWN ACTIVATED: {reason}"
5. Only available commands in lockdown: HELP, STATUS, HEAL_DIAGNOSE, SECURITY_AUDIT
6. Lockdown remains until user explicitly runs: `> OS_COMMAND SECURITY_LOCKDOWN --lift`

---

## What This Skill Is (and Isn't)

This skill is a **pre-mutation security checklist** — it uses the LLM's reasoning
to catch common security issues before code is written to disk. It is good at:
- Catching hardcoded credentials and secrets
- Spotting obvious injection patterns and unsafe function calls
- Flagging suspicious dependencies
- Enforcing a security-conscious workflow

It is **NOT a substitute for production-grade static analysis tools**. For CI/CD
pipelines and production security, integrate dedicated SAST tools like:
- **Secrets**: `gitleaks`, `trufflehog`
- **SAST**: `semgrep`, `snyk`, `codeql`
- **Dependency audit**: `npm audit`, `pip-audit`, `cargo audit`

The `INFRA_SETUP_CI` command can scaffold these integrations for you.

## Common Mistakes

1. **Skipping review for "trivial" changes** — Even a one-line change can introduce a secret leak. The review is mandatory.
2. **Relying solely on this skill for production security** — Use dedicated SAST tools in your CI pipeline.
3. **Assuming dependencies are safe** — Transitive dependencies can introduce vulnerabilities the direct dependency doesn't have.
