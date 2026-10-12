---
name: context-engine
description: >-
  Context assembly, relevance scoring, token budget management, and context
  pruning. Addresses a common failure mode in agentic coding — loading the wrong
  context, not reasoning incorrectly — by helping the agent have the right
  information at the right time within token budget constraints.
---

# Context Engineering Engine

## Overview

What context gets loaded is often as consequential as how the prompt is worded — a
correct-sounding answer built on stale or irrelevant context is still wrong. This skill
governs context assembly directly: loading exactly what's needed, scoring relevance,
managing token budgets, and pruning low-value information.

The core principle: **Minimum Viable Context** — load the minimum set of tokens that
maximizes the probability of a correct response.

**Scope note**: on most hosts (Claude Code, Cursor, IDE agents), the host — not this
skill — manages your actual context window and token accounting; you cannot query a
precise remaining-budget number, and CONTEXT_BUDGET below should be read as a qualitative
self-check, not a metered readout. What this skill genuinely controls is *what you choose
to read* — that's real leverage regardless of host.

## Commands

### CONTEXT_LOAD

Assemble optimal context for a task.

```
> OS_COMMAND CONTEXT_LOAD --task=<description> [--budget=<max_tokens>]
```

**Procedure:**
1. Identify task-critical dependencies; score sources with CONTEXT_SCORE when useful.
2. Run `python .ai-os/scripts/ai_os.py pack --snapshot --render` with repeated
   `--skill <registered-id>` and `--file <workspace-path>` for relevant sources only.
   CLI `--task` names an original branch/ad-hoc identity; it is not the task description.
3. The assembler pins governance, active task, and active plan before optional sources,
   deduplicates by stable source ID, hashes raw sources, and renders deterministically.
4. Record the snapshot path (canonical pack JSON hash under memory/runtime/snapshots).
   `diff <before> <after>` explains added/removed/changed sources; `replay <snapshot>`
   reproduces AI-OS text independent of current files.
5. Report source count and bytes/characters. Any character-to-token conversion is an
   estimate; provider usage statistics are authoritative. Large context windows do not
   justify loading whole modules automatically. Optional selection never removes governance.

**Priority order for context assembly:**
1. **Task-critical files** — Files directly mentioned or clearly needed for the task
2. **Active code patterns** — Relevant entries from `memory/semantic/patterns.json`
3. **Recent decisions** — Last 3-5 relevant entries from `decisions.jsonl`
4. **Project knowledge** — Relevant sections from `project_knowledge.md`
5. **Procedural memory** — Matching workflows from `workflows.json`
6. **Related test files** — Tests for modules being modified
7. **Configuration files** — Relevant configs for affected systems

---

### CONTEXT_SCORE

Score file relevance to current task.

```
> OS_COMMAND CONTEXT_SCORE --task=<description> --files=<file1,file2,...>
```

**Scoring factors:**
| Factor | Weight | Description |
|---|---|---|
| Direct mention | 1.0 | File is explicitly mentioned in the task |
| Same directory | 0.7 | File is in the same directory as a target file |
| Import chain | 0.6 | File imports or is imported by a target file |
| Recent modification | 0.5 | File was modified in the last session |
| Name match | 0.4 | File name contains task-relevant keywords |
| Test file for target | 0.8 | File is the test for a file being modified |
| Config for target | 0.6 | File configures a system being modified |
| Unrelated module | 0.1 | No clear connection to the task |

**Output:** Ranked list of files with relevance scores (0.0 – 1.0).

---

### CONTEXT_BUDGET

Check token budget and recommend what to load or prune.

```
> OS_COMMAND CONTEXT_BUDGET [--estimate-file=<path>]
```

**Procedure:**
1. Give a rough, self-reported estimate of what you've loaded so far (this is an estimate,
   not a metered figure — say so).
2. If `--estimate-file`: estimate the token cost of loading the specified file (roughly:
   file size in characters / 4).
3. Recommend action qualitatively: "Looks fine" / "Consider pruning low-relevance items
   before loading more" — don't imply precision you don't have.

---

### CONTEXT_PRUNE

Remove low-value context to make room for high-value information.

```
> OS_COMMAND CONTEXT_PRUNE [--aggressive]
```

**Pruning priority (remove first):**
1. Old session data (episodic entries older than current session)
2. Generic patterns not relevant to current task
3. Procedural memory for unrelated workflows
4. Semantic knowledge for unrelated project areas
5. *(Never prune)* Task-critical files and active code

Assemble a new pack with fewer optional sources and inspect its diff. Keep pinned
sources. Report only the pack-size reduction; this cannot erase messages already sent,
free a claimed percentage of the provider context, or force host compaction. Use the
host's supported clear/compaction controls when needed, then reload the current pack.

---

## Context Engineering Principles

### 1. Write-Select-Compress-Isolate

The four pillars of context engineering:
- **Write**: Externalize state to memory files (don't try to remember everything in context)
- **Select**: Load only relevant information for the current task
- **Compress**: Summarize large documents rather than loading them whole
- **Isolate**: Keep system instructions separate from data content

### 2. Context Pollution Prevention

- Don't load entire files when only a function is needed
- Don't load all memory when only recent decisions matter
- Don't load test files for modules you're not modifying
- Select a fresh pack before switching tasks; host controls clear/compaction

### 3. Adaptive Context Strategy

Context strategy adapts based on project genome:
| Architecture | Strategy |
|---|---|
| `single-app` | Load broadly — most files are relevant |
| `monorepo-fullstack` | Load narrowly — scope to the specific app/service |
| `library` | Load API surface + tests for the modified module |
| `api-service` | Load endpoint handlers + middleware + relevant models |
| `data-pipeline` | Load pipeline stage + upstream/downstream connections |

## Common Mistakes

1. **Loading everything** — More context ≠ better results. Precision matters more than volume.
2. **Ignoring token budget** — Running out of context budget mid-task degrades reasoning quality.
3. **Not pruning between tasks** — Leftover context from the previous task pollutes the current one.
