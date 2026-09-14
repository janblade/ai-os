---
name: observability-audit
description: >-
  Decision logging, action tracing, session export, progress reporting, and
  system health dashboards. Provides transparency and an audit trail inspired
  by ISO/IEC 42001 principles and the AI OS governance framework.
---

# Observability & Audit Trail

## Overview

The observability skill ensures transparency — every significant decision, action,
and system state change is logged and auditable. This skill is the backbone of
the governance framework's transparency requirements, inspired by ISO 42001 principles.

## Commands

### LOG_DECISION / LOG_ACTION

Record a decision or action to episodic memory. Both use the same minimal schema —
there is no meaningful distinction worth two record shapes; `type` carries it.

```
> OS_COMMAND LOG_DECISION --decision=<text> --rationale=<text>
> OS_COMMAND LOG_ACTION --action=<text> --reason=<text> [--files=<affected>]
```

**Schema — the only shape written to `decisions.jsonl`:**
```json
{"ts": "2026-08-02T10:00:00+08:00", "type": "decision|action|evolution|conflict", "what": "...", "why": "...", "files": ["..."]}
```

- `what` = the decision text or the action text.
- `why` = the rationale or reason.
- `files` is optional — omit it if nothing was touched.
- Deliberately **no** `confidence`, `alternatives_considered`, `outcome`, or `session_id`
  fields. In practice these were never kept current after being written (confidence was
  always `1.0`, outcome was always `pending`) — they cost tokens on every entry and every
  future read for no real signal. If you genuinely have 2+ alternatives worth recording
  for a significant architectural call, fold a one-clause summary into `why` instead of a
  separate structured field.

Append one line. Confirm briefly: "Logged: {what}".

---

### TRACE_SESSION

Export a session's trace for audit.

```
> OS_COMMAND TRACE_SESSION [--since=<ISO timestamp>] [--format=json|markdown]
```

**Procedure:**
1. Collect `decisions.jsonl` entries with `ts` at or after `--since` (default: the `started`
   timestamp of the most recent entry in `sessions.jsonl`) — entries are matched by time
   range, not a session ID, since decision records don't carry one.
2. Pair with the matching `sessions.jsonl` entry for duration/summary metadata.
3. Format as requested (JSON for machine processing, Markdown for human review).
4. Write to `.ai-os/memory/episodic/trace_{date}.{ext}`.

---

### REPORT_PROGRESS

Generate a progress report from logs.

```
> OS_COMMAND REPORT_PROGRESS [--period=today|week|all]
```

**Procedure:**
1. Read recent entries from `decisions.jsonl`
2. Read evolution proposals from `progress.md`
3. Summarize:
   - Tasks completed
   - Decisions made (with rationale summaries)
   - Evolutions proposed/applied
   - Security scans run and findings
   - Open items and next steps
4. Update `progress.md` with the report

---

### REPORT_HEALTH

System-wide health dashboard.

```
> OS_COMMAND REPORT_HEALTH
```

**Procedure:**
1. **Boot status**: last boot time, boot count, integrity result
2. **Archetype**: active archetype and governance level
3. **Skills**: derive health from `decisions.jsonl` — count recent `type: "action"` entries per skill that read as failures/repairs (see `HEAL_CIRCUIT_STATUS` in `core.self-healing.sk`); there is no live per-skill state file to read
4. **Memory**: size of each memory store, last updated timestamps
5. **Security**: last scan time, open findings count
6. **Evolutions**: total applied, pending proposals, last evolution
7. **Project Genome**: detected stack summary

**Output:** Formatted health dashboard.

---

## Automatic Logging

The observability skill is invoked automatically by other skills:
- **Security skill**: logs scan results after every SECURITY_AUDIT/SCAN_FILE
- **Evolution skill**: logs every proposal, application, and rollback
- **Self-healing skill**: logs diagnoses and repairs
- **Boot sequence**: does *not* log at boot (nothing has happened yet) — logs once at
  session wrap via `MEMORY_CONSOLIDATE` or `TASK_CLOSE` (see `BOOT.md` §9)

## Common Mistakes

1. **Logging too much detail** — Keep entries concise. Reference files rather than embedding content.
2. **Forgetting to log decisions** — If you chose between alternatives, log it. Future sessions need this context.
3. **Not reviewing logs** — Logs are useful only if read. Regularly review via REPORT_PROGRESS.
