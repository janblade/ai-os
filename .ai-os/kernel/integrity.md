# Kernel Integrity Protocol

> Lightweight self-check for Boot §2. This is a structural sanity check an
> agent can actually perform by listing files — not a cryptographic
> verification. There is no integrity hash; nothing in this framework can
> compute or check one without a tool the host may not offer, so we don't
> pretend to.

## Required Directory Structure

### Kernel Space (Immutable)
```
.ai-os/BOOT.md
.ai-os/manifest.json
.ai-os/kernel/integrity.md
.ai-os/kernel/bootstrap.md
.ai-os/rules/ultimate_rules.md
.ai-os/rules/security_policy.md
.ai-os/rules/evolution_policy.md
.ai-os/genome/archetypes/index.json
.ai-os/genome/archetypes/hobby.json
.ai-os/genome/archetypes/startup.json
.ai-os/genome/archetypes/enterprise.json
.ai-os/genome/archetypes/critical.json
```

### User Space (Evolvable)
```
.ai-os/genome/project_genome.json
.ai-os/memory/episodic/decisions.jsonl
.ai-os/memory/episodic/sessions.jsonl
.ai-os/memory/episodic/last_session.json
.ai-os/memory/semantic/project_knowledge.md
.ai-os/memory/semantic/patterns.json
.ai-os/memory/semantic/knowledge/architecture_overview.md
.ai-os/memory/semantic/knowledge/conventions_patterns.md
.ai-os/memory/semantic/knowledge/known_gotchas.md
.ai-os/memory/tasks/
.ai-os/memory/archived_tasks/
.ai-os/memory/procedural/workflows.json
.ai-os/memory/procedural/playbooks.md
.ai-os/registry/index.json
.ai-os/registry/core.security.sk/SKILL.md
.ai-os/registry/core.infra.sk/SKILL.md
.ai-os/registry/core.testing.sk/SKILL.md
.ai-os/registry/core.evolution.sk/SKILL.md
.ai-os/registry/core.observability.sk/SKILL.md
.ai-os/registry/core.context-engine.sk/SKILL.md
.ai-os/registry/core.self-healing.sk/SKILL.md
.ai-os/registry/core.architect.sk/SKILL.md
.ai-os/registry/core.memory.sk/SKILL.md
.ai-os/registry/core.planning.sk/SKILL.md
.ai-os/registry/core.dev-loop.sk/SKILL.md
.ai-os/registry/core.simplicity.sk/SKILL.md
.ai-os/scripts/session-start-hook.sh
.ai-os/agents/index.json
.ai-os/agents/supervisor.json
.ai-os/agents/templates/web_developer.json
.ai-os/agents/templates/api_developer.json
.ai-os/agents/templates/qa_auditor.json
.ai-os/commands/index.json
.ai-os/commands/aliases.json
.ai-os/progress.md
```

## Checks (run when something seems broken, not every boot)

1. **Structure**: paths above exist. Missing user-space file → recreate from default. Missing kernel-space file → report to user, do not silently recreate (you may be looking at a corrupted or tampered kernel).
2. **Manifest schema**: `manifest.json` has `ai_os_version`, `project_archetype` (one of `auto|hobby|startup|enterprise|critical`), `security_level`, `installed_skills`.
3. **Registry consistency**: every `registry/index.json` entry has a matching `.sk/SKILL.md` on disk. Orphaned entries → remove. Missing entries → add.
4. **Parseability**: `.jsonl` files have valid JSON per line (empty file is valid); `.json` files parse; `.md` files are readable text.

## Failure Response

| Severity | Condition | Response |
|---|---|---|
| **WARN** | Non-critical user-space file missing | Recreate from default, continue |
| **ERROR** | Kernel-space file missing | Report to user, do not proceed with autonomous changes until resolved |
| **CRITICAL** | Manifest corrupt or multiple kernel files missing | Restrict yourself to `HELP`, `STATUS`, `HEAL_DIAGNOSE`, `HEAL_REPAIR` until the user resolves it |
