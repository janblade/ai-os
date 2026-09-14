---
name: infra-scaffolding
description: >-
  Tech stack detection, project scaffolding, CI/CD pipeline generation, health
  diagnostics, and deep project analysis. The infrastructure skill understands
  your project's shape and helps you build, verify, and deploy it.
---

# Infrastructure & Scaffolding

## Overview

The infra skill is the "hands" of the AI OS — it detects what you're working with,
scaffolds what you need, generates CI/CD pipelines, and runs health checks to verify
everything is working correctly.

## Commands

### INFRA_DETECT_STACK

Auto-detect the project's tech stack and architecture.

```
> OS_COMMAND INFRA_DETECT_STACK [--deep]
```

**Procedure:**
1. Scan workspace root for indicator files (see BOOT.md §2 Phase 3)
2. Parse detected config files for framework/library information
3. Identify architecture pattern (monorepo, single-app, library, API, CLI, etc.)
4. Assess project maturity indicators (README, license, CI, tests, contributors)
5. Write results to `genome/project_genome.json`
6. If `--deep`: Also analyze code structure for patterns, entry points, and module boundaries

**Output:** Project genome summary with detected stack, architecture, and maturity.

---

### INFRA_SCAFFOLD

Generate project structure from best practices.

```
> OS_COMMAND INFRA_SCAFFOLD --type=<project_type> [--stack=<stack>]
```

**Types:** `web-app`, `api-service`, `library`, `cli-tool`, `monorepo`, `fullstack`

**Procedure:**
1. Select template based on project type and detected/specified stack
2. Generate directory structure following stack-specific best practices:
   - Source directories, test directories, config files
   - README template, LICENSE selection, .gitignore
   - Linter/formatter configuration
   - TypeScript config (if applicable)
3. Initialize package manager (npm init, uv init, cargo init, etc.)
4. Present generated structure to user for approval before writing

---

### INFRA_SETUP_CI

Generate CI/CD pipeline configuration.

```
> OS_COMMAND INFRA_SETUP_CI --platform=<platform> [--stages=<stages>]
```

**Platforms:** `github-actions`, `gitlab-ci`, `azure-devops`, `circleci`

**Stages** (comma-separated): `lint`, `type-check`, `test`, `security-scan`, `build`, `deploy`

**Procedure:**
1. Detect project stack (or use cached genome)
2. Generate platform-specific pipeline configuration:
   - CI file with requested stages
   - Appropriate runner/image selection
   - Caching configuration for dependencies
   - Branch/PR trigger rules
3. Include AI OS security scan as a pipeline stage
4. Present generated config for user review

---

### INFRA_HEALTH_CHECK

Quick project health verification.

```
> OS_COMMAND INFRA_HEALTH_CHECK
```

**Procedure:**
1. **Build check**: Can the project build successfully?
2. **Lint check**: Do linting tools pass?
3. **Type check**: Do type checkers pass? (if applicable)
4. **Test check**: Do tests pass?
5. **Dependency check**: Are dependencies installed and lock file up to date?

**Output:** Health dashboard with pass/fail for each check.

---

### INFRA_DIAGNOSE

Deep project diagnostic.

```
> OS_COMMAND INFRA_DIAGNOSE [--focus=<area>]
```

**Focus areas:** `dependencies`, `build`, `tests`, `config`, `structure`, `all`

**Procedure:**
1. Run all HEALTH_CHECK verifications
2. Analyze dependency tree for issues (circular deps, outdated, deprecated)
3. Check configuration file consistency
4. Verify directory structure matches detected architecture pattern
5. Check for common anti-patterns (mixed config styles, orphaned files, etc.)
6. Generate detailed diagnostic report with recommendations

---

### INFRA_DISCOVER_MODULES

Discover distinct codebase modules and trigger auto-generation of modular workspace skills.

```
> OS_COMMAND INFRA_DISCOVER_MODULES [--auto-scaffold]
```

**Procedure:**
1. Scan directories down to depth 2 (excluding node_modules, .git, .ai-os, build/dist).
2. Identify distinct modules based on presence of stack-specific markers:
   - Directory containing its own `package.json`, `Cargo.toml`, `pyproject.toml`, `requirements.txt`, `go.mod`, etc.
   - Distinct logical subfolders (e.g. `frontend/`, `backend/`, `api/`, `services/`, `db/`).
3. For each discovered module:
   - Identify the name (e.g., `moonlight-web` or `api-service`).
   - Check if a corresponding skill folder (e.g., `/.ai-os/registry/moonlight-web.sk/`) and custom agent profile (e.g., `/.ai-os/agents/moonlight-web.json`) exist.
   - If missing and `--auto-scaffold` is enabled: Trigger `EVOLVE_PROPOSE` to auto-scaffold:
     1. A customized skill containing commands (like `DEV`, `BUILD`, `TEST`) scoped to that folder.
     2. A synthesized agent profile. If a template matches, use it; otherwise, synthesize a new profile:
        - Analyze module packages (e.g. `pytorch` in python → synthesize "Data Scientist/ML Specialist").
        - Generate a custom specialized `system_prompt_extension` describing the language features and best practices for the detected libraries.
        - **Capability check first** (same principle `core.dev-loop.sk`'s `DEV_IMPLEMENT_REVIEWED` applies to subagent dispatch): directory-bounded sandboxed execution and per-agent model-tier pinning are host tool capabilities, not something every agentic AI can enforce. Confirm the host actually exposes a mechanism for either before writing them into the profile as if they'll be enforced. Host supports it → configure it for real. Host doesn't → record the *intent* (preferred model tier, intended directory scope) as advisory text in `system_prompt_extension` instead, and say so plainly in the report — never claim a sandboxing or tier-assignment guarantee the host can't actually back.
4. Report list of discovered modules, skill status, and agent profile synthesis status — including, per synthesized profile, whether directory-scoping/model-tier were host-enforced or only recorded as advisory.

---

### INFRA_SHOW_ENV

Show environment variables and configurations of the current workspace.

```
> OS_COMMAND INFRA_SHOW_ENV [--file=<config_file>]
```

**Procedure:**
1. Locate workspace environment configuration files (e.g. `.env`, `.env.local`, `config.json`, project settings).
2. Scan active environment variables related to the project.
3. Check for structural or configuration mismatch warnings.
4. Output a formatted list of environment configurations (masking credentials to prevent leaks in compliance with Rule R11).

---

### INFRA_SWITCH_ENV

Switch the active workspace configuration or release environment profile.

```
> OS_COMMAND INFRA_SWITCH_ENV --profile=<profile_name> [--target-file=<destination_file>]
```

**Procedure:**
1. Check if the specified environment profile file exists (e.g. `.env.development`, `.env.production`).
2. Backup the current active configuration file.
3. Swap/overwrite the active configuration target file (defaults to `.env`) with the selected profile source.
4. Run `INFRA_HEALTH_CHECK` to verify that the workspace builds and runs under the new profile.

---

### INFRA_ANALYZE_COMMITS

Analyze recent Git merge commits or branch history to extract architectural decisions, conventions, and gotchas with temporal reconciliation.

```
> OS_COMMAND INFRA_ANALYZE_COMMITS [--count=<N>] [--mode=merges-only|all-commits] [--supersede-check]
```

**Parameters:**
- `--count` (default: `10`): Number of recent merge commits (or commits) to fetch and analyze.
- `--mode` (default: `merges-only`): Mode of analysis:
  - `merges-only` (default): Focus exclusively on merge commits/PRs to main/master (`git log --first-parent main -n <N>`) for maximum signal-to-noise ratio.
  - `all-commits`: Raw commit history scan fallback.
- `--supersede-check` (default: `true`): Enable temporal reconciliation to detect when a newer merge commit reverts, updates, or supersedes knowledge introduced by an older merge.

**Procedure:**
1. Determine active primary branch (`main`/`master`/`develop`).
2. If `--mode=merges-only`: first check `git log --merges <primary_branch> -n 1` — empty means this
   repo has no real merge commits (common on `hobby`-archetype/solo projects with no PR workflow;
   `--first-parent` on a merge-free branch silently returns the same linear log as `all-commits`
   while still labeling itself "merges-only," which misrepresents that no filtering happened). Empty
   → tell the user no merge commits were found and either fall back to `all-commits` explicitly
   (labeled as such in the output, not silently) or ask, rather than proceeding as if the filter
   engaged. Non-empty → execute `git log --first-parent <primary_branch> -n <N> --stat` to retrieve
   PR/merge descriptions, diff summaries, and merge author dates. If `--mode=all-commits`: run
   `git log -n <N> --stat` directly, no merge check needed.
3. Group merge commits in chronological order (oldest to newest).
4. **Temporal Reconciliation & Extraction Pass**:
   - Extract high-level architectural shifts, design decisions, conventions, and gotchas from PR merge messages and diffs.
   - Cross-reference newer merges against earlier ones: if a newer merge changes or deprecates a pattern established in an older merge, mark the old pattern as **SUPERSEDED** and retain only the active pattern.
5. **Knowledge Routing**:
   - Route active architectural facts to `memory/semantic/knowledge/architecture_overview.md`.
   - Route active conventions to `memory/semantic/knowledge/conventions_patterns.md`.
   - Route active gotchas or bug fixes to `memory/semantic/knowledge/known_gotchas.md`.
   - Ensure target sub-files are properly indexed in `project_knowledge.md`.
6. Log execution in `memory/episodic/decisions.jsonl`.


---

### INFRA_MAP_DATAFLOW

Trace where a piece of data comes from and everywhere it ends up (or, run backward: what can write to a given destination) — built for bug triage and change-impact analysis, not as a standing full-project index.

```
> OS_COMMAND INFRA_MAP_DATAFLOW --field=<name>      # forward: input -> every place it's read, transformed, and emitted
> OS_COMMAND INFRA_MAP_DATAFLOW --sink=<name>        # backward: DB column / endpoint / file -> every input that can reach it
> OS_COMMAND INFRA_MAP_DATAFLOW --all [--scope=<module>]  # explicit full-project/full-module pass — see cost guardrail
```

**Procedure:**
0. **A bare invocation (no `--field`, `--sink`, or `--all`) is not a full-project trace — it's an incomplete request.** Typing just `trace` doesn't mean "find everything"; ask what field or sink to trace rather than guessing, the same way an ad-hoc task name gets asked for instead of invented (`BOOT.md` §2 step 4). Only treat it as a full-project request if the user actually said something to that effect ("map all the data flows," "trace everything") — that's what `--all` is for, and it still goes through the cost guardrail below.
1. Resolve the starting symbol at the relevant boundary — form field/route param for `--field`, schema/migration column or outbound call site for `--sink`.
2. **Check the cache before doing any fresh work.** Look up this exact symbol in `memory/semantic/generated/<project_name>_dataflow_map.json` (`project_name` from `manifest.json`). If an entry exists and its tagged commit SHA matches current `git rev-parse HEAD`, **and** `git status --porcelain` reports a clean tree, report that cached trace directly (noting the commit/timestamp it's from) instead of re-deriving — this is the entire point of caching; skipping this check would make the cache write in step 8 pointless. If the SHA matches but the tree is dirty, still show the cached trace (don't force an expensive re-trace over unrelated local edits) but caveat it plainly: "cached as of `<sha>`, you have uncommitted changes that may not be reflected — re-run if your edits touch this flow." If the entry is stale (different commit) or absent, continue to a fresh trace.
3. Check `memory/semantic/knowledge/conventions_patterns.md` for any project-specific sink resolutions already learned (e.g. "`Outbox.publish` wraps a Kafka producer, category=queue") before falling back to the generic catalog below — this is what makes fresh traces on the same project sharper over time.
4. Walk the call chain outward from the symbol, hop by hop (VS Code Call Hierarchy API when the host exposes it, grep-based "who calls this" otherwise), checking each hop against the **Sink Pattern Catalog**. Cap traversal at ~5 hops to bound cost — this traversal is a sub-routine of this command, not a standalone call-graph feature.
5. Label every finding with its own confidence — do not give the whole trace one blanket rating:
   - **High**: direct match against a known sink pattern in the catalog or a learned project-specific pattern.
   - **Low**: chain reaches a call this command can't resolve further (external library with no catalog entry, hop cap reached, or dynamic/reflective dispatch) — report as "unresolved beyond this point, verify manually."
6. If the project already has a real dataflow/taint tool configured (CodeQL, Semgrep with dataflow rules, etc.), prefer running that for the whole trace instead of steps 4-5, and say so in the output. Otherwise the result is a name/pattern-based approximation — label it that way; never present it at the same confidence as a real tool's output.
7. Report the trace directly to the user for triage. This step alone does **not** write to semantic memory.
8. Write/overwrite this symbol's entry in `memory/semantic/generated/<project_name>_dataflow_map.json`, tagged with tool tier used, git commit SHA, and timestamp — this is what step 2 checks on the next call. This file is read only by this command, only when it runs — it is not part of the boot sequence (`BOOT.md` §2 step 3 reads only `last_session.json`) and not in `core.context-engine.sk`'s on-demand load order, so it never adds to boot or routine context cost regardless of how large it grows.
9. Only if the user confirms a finding is durable (or a custom sink got resolved along the way), promote it through `core.memory.sk`'s existing verify/accept gate: a resolved custom sink pattern goes to `conventions_patterns.md`; a load-bearing data-flow fact about a major entity goes to `architecture_overview.md`, capped to what's actually notable (not the full dictionary), with a pointer back to the cached artifact and an "as of commit `<sha>`" freshness marker.
10. Log execution in `memory/episodic/decisions.jsonl`.

**Cost guardrail:** `--all` (explicit full-project pass) is only appropriate for small codebases — otherwise require it be paired with `--scope=<module>`, or warn about cost and get confirmation before running one unscoped.

**Sink Pattern Catalog** (default patterns — extend via learned entries in `conventions_patterns.md`, not by editing this table per project):

| Category | Example patterns (by ecosystem) |
|---|---|
| **Database** | `INSERT`/`UPDATE`/`SELECT` SQL, `*.save()`/`*.create()`/`*.query()` (ORM: Sequelize, SQLAlchemy, ActiveRecord, GORM, Entity Framework), migration/schema column definitions |
| **Outbound HTTP/API** | `axios.*`, `fetch(`, `requests.*`, `http.Client`, `HttpClient`, `RestTemplate`, gRPC client stubs |
| **Message queue** | `producer.send`, `channel.publish`, `sqs.sendMessage`, pub/sub client `.publish(`, Kafka/RabbitMQ/SNS/SQS client calls |
| **File / blob storage** | `fs.writeFile`, `open(...,'w')`, `s3.putObject`, Blob/GCS client `.upload(`/`.save(` |
| **Cache** | `redis.set`, `memcached.set`, cache client `.set(`/`.put(` |
| **Email / notification** | mail client `.send(`, webhook POST calls, push-notification SDK `.send(` |

**Common failure mode this command is explicitly designed around:** custom in-house wrappers around a real sink (an internal `db.write()` helper, an `Outbox` abstraction) won't match the catalog and won't be followed past one hop without help — that's exactly what step 2's learned-pattern lookup and step 4's per-hop confidence labeling exist to surface honestly instead of silently under- or over-claiming coverage.

---

### INFRA_WORKTREE_START

Create a physically isolated working directory for a branch, instead of relying on
branch-name-sanitized task files alone for isolation.

```
> OS_COMMAND INFRA_WORKTREE_START --branch=<name> [--base=<ref>]
```

**Procedure:**
1. Confirm the workspace is a git repo (`git rev-parse --is-inside-work-tree`) — if not,
   report that worktrees aren't applicable here rather than failing silently.
2. Determine the sibling directory path: `../<repo-name>-<sanitized-branch>` (same branch
   sanitization rule as `BOOT.md` §2 step 4 — `/` and path-unsafe chars → `_`).
3. If `--branch` doesn't exist yet, create it from `--base` (default: current branch) as
   part of the `git worktree add` invocation; if it already exists, attach to it.
4. Run `git worktree add <path> <branch>` (or `git worktree add -b <branch> <path> <base>`
   for a new branch).
5. Report the new path to the user. From here, normal task-memory flow applies unchanged:
   `BOOT.md` §2 step 4 loads/creates `memory/tasks/[sanitized_branch].md` — worktrees add
   filesystem isolation on top of that, they don't replace it.

**Note:** this is a plain `git worktree` invocation — no host-specific capability assumed,
any host with shell access can run it (contrast `core.dev-loop.sk`'s `DEV_IMPLEMENT_REVIEWED`,
which does depend on host subagent support).

---

### INFRA_WORKTREE_FINISH

Remove a worktree once its branch is merged or abandoned.

```
> OS_COMMAND INFRA_WORKTREE_FINISH --branch=<name> [--force]
```

**Procedure:**
1. Locate the worktree path for `--branch` via `git worktree list`.
2. Check for uncommitted changes in that worktree (`git -C <path> status --porcelain`) —
   non-empty and `--force` not given → stop, tell the user what's uncommitted (R20:
   confirm before discarding uncommitted work).
3. Run `git worktree remove <path>` (`--force` only if the user explicitly passed it, per
   step 2's gate).
4. Does **not** delete the branch itself or the task file — that's `TASK_CLOSE`'s job, not
   this command's. Removing the worktree only cleans up the filesystem-level isolation.

---

## Stack-Specific Best Practices

The infra skill references these best practices based on detected stack:

| Stack | Key Practices |
|---|---|
| **Node.js/TypeScript** | ESLint + Prettier, strict tsconfig, path aliases, barrel exports |
| **Python** | Ruff/Black formatting, mypy type checking, pyproject.toml over setup.py |
| **Rust** | Clippy lints, cargo fmt, workspace layout for multi-crate projects |
| **Go** | golangci-lint, go vet, standard project layout |
| **Java/Kotlin** | Checkstyle/ktlint, Gradle over Maven for new projects, JUnit 5 |
| **.NET/C#** | dotnet format, nullable reference types, minimal APIs |

## Common Mistakes

1. **Scaffolding before detecting** — Always run INFRA_DETECT_STACK first on existing projects.
2. **Overwriting existing CI** — Always check for existing pipeline files before generating new ones.
3. **Ignoring health check warnings** — A "passing" health check with warnings still has issues to address.
