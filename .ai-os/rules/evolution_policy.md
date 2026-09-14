# Evolution Policy — Self-Update Constraints & Gates

> Governs how the AI OS evolves itself: what can change, who approves, how to roll back.

---

## Evolution Boundaries

### Kernel Space — IMMUTABLE (human + `KERNEL OVERRIDE AUTHORIZED` only)

| File | Why Protected |
|---|---|
| `BOOT.md` | Core identity/boot protocol — changing this changes everything |
| `manifest.json` | Project identity — only `boot_count`/`last_boot`/`tech_stack`/`evolution_history` auto-update |
| `kernel/integrity.md` | Self-verification — modifying this could mask corruption |
| `rules/ultimate_rules.md` | Core governance — self-modification = circular authority |
| `rules/security_policy.md` | Security posture — agent modifying security = fox guarding henhouse |
| `rules/evolution_policy.md` | This file — modifying evolution rules from within = infinite loop |
| `genome/archetypes/*.json` | Governance profiles — pre-defined calibration points |

Auto-updatable exceptions (no override needed): `manifest.json.boot_count`, `.last_boot`,
`.tech_stack`, `.evolution_history`.

Bypass mechanism (per-action and session-scoped) is defined in `rules/ultimate_rules.md`
R3 — this table defines *what* is protected, R3 defines *how* protection can be lifted.

### User Space — EVOLVABLE

| Target | Create | Update | Delete | Approval |
|---|---|---|---|---|
| New skill (`.sk/`) | ✅ | ✅ | ✅ | Auto (log only) |
| `security.sk` | ❌ | ⚠️ | ❌ | Human review ALWAYS |
| `registry/index.json` | — | ✅ | — | Auto (mirrors disk) |
| `commands/index.json` | — | ✅ | — | Auto (mirrors disk) |
| `commands/aliases.json` | — | ✅ | — | Auto (log only) |
| Memory files (all) | ✅ | ✅ | ✅ | Auto |
| `project_genome.json` | — | ✅ | — | Auto (perception scan) |
| `progress.md` | — | ✅ | — | Auto |

---

## Authoring Style for Kernel-Space Content

New/edited `BOOT.md` or `rules/*.md` content is written AI-first from the start — dense
fragments, arrows, pipe-lists, no narrative prose — not written readable-first and
compacted in a later pass. Reader is an AI agent, not a human; optimize for unambiguous
parsing + token cost. Template: `rules/ultimate_rules.md` R15. Every disambiguating
specific (exceptions, exact archetype behavior, concrete cross-references) still MUST
survive intact — only narrative connective tissue and restatement get cut.

---

## Evolution Lifecycle (PDCA)

### 1. PLAN — Proposal
```markdown
## Evolution Proposal: EP-{n}
- Date: {ISO 8601}
- Type: {skill_create|skill_update|command_create|command_update|memory_update|kernel_update|workflow_optimization}
- Target: {file/skill}
- What: {change}
- Why: {rationale}
- Risk: {low|medium|high}
- Rollback Plan: {how to undo}
- Rules Check: {rules touched, confirm no violations}
- Status: PROPOSED|APPROVED|APPLIED|ROLLED_BACK|REJECTED
```

### 2. DO — Apply
- Low risk, non-security → apply immediately, log in `decisions.jsonl`.
- Medium risk → present proposal, apply after acknowledgment.
- High risk or security-related → present proposal, wait for explicit "approved"/"proceed".
- Kernel space → refuse; inform user `KERNEL OVERRIDE AUTHORIZED: {files}` (per-action) or
  `KERNEL OVERRIDE AUTHORIZED FOR SESSION: {scope}` (standing grant, R3) is required.

### 3. CHECK — Verify
1. Integrity check — all files parse.
2. No rules violated by the change.
3. Skill modified → invoke it with a test command to verify it works.
4. Fail → immediate rollback (step 4).

### 4. ACT — Commit or Rollback
Pass:
- Update `registry/index.json` / `commands/index.json` if skills/commands changed.
- Log to `memory/episodic/decisions.jsonl`, unified schema (R13, `BOOT.md` §9):
  ```json
  {"ts": "...", "type": "evolution", "what": "EP-{n}: ...", "why": "...", "files": ["..."]}
  ```
- Update `progress.md` with outcome.
- Increment `manifest.json.evolution_history.total_evolutions`.
  Note: `total_evolutions` and the highest EP-ID in `progress.md` can legitimately diverge
  — EP-IDs are assigned sequentially to every proposal written, but the counter only
  increments for proposals that actually reached APPLIED and touched `.ai-os/` payload
  content. A proposal that stayed PROPOSED, was rolled back, or only touched files outside
  `.ai-os/` (e.g. `README.md`/installer-docs-only changes) consumes an ID without bumping
  the counter. A growing gap isn't itself a bug — verify against `progress.md`'s actual
  Status fields before assuming the counter is stale.

Fail:
- Restore the previous version of affected file(s).
- Log the rollback, same schema: `{"ts": "...", "type": "evolution", "what": "EP-{n}: rolled back — {reason}", "why": "..."}`.
- Proposal status → `ROLLED_BACK`. Report failure to user with details.

---

## Rollback Protocol

AUTOMATIC (verification failure): evolution skill preserves pre-change content before
applying → restore on failure → log the rollback → no manual intervention needed.

MANUAL (user-requested revert of a past evolution): look up the EP ID in
`decisions.jsonl` → previous version available → restore it; not available → inform
user, suggest manual fix. Run integrity check after either path.

---

## Rate Limiting Evolutions

Max 5 evolutions per conversation without explicit user acknowledgment — countable
(visible in this conversation's own history), unlike token/step counts. After 5, pause
and summarize all changes made. "Continue evolving" resets the counter.

---

## Forbidden Evolutions

Never permitted for the agent to do unilaterally — no archetype setting relaxes any of
these, and `KERNEL OVERRIDE AUTHORIZED` is the floor, not a bypass, for #1:
1. Modifying this file without `KERNEL OVERRIDE AUTHORIZED` (with it: human-directed
   only, never agent-initiated).
2. Removing or weakening security scan requirements.
3. Increasing the agent's own permission boundaries.
4. Disabling logging or audit trail.
5. Modifying existing rules without `KERNEL OVERRIDE AUTHORIZED`.
6. Bypassing human approval gates for a lower archetype level.
