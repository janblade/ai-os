---
name: architect
description: >-
  Transforms a raw idea into a fully planned and scaffolded project. Handles the
  complete journey from concept to code-ready workspace: requirements gathering
  through structured interview, tech stack selection, architecture design,
  feature breakdown, milestone planning, and automated project scaffolding.
  Use when the user has an idea but no project yet.
---

# Architect — From Idea to Project

## Overview

The Architect skill handles the greenfield scenario: the user has an idea but no
code, no project, no structure. This skill interviews the user, designs the
architecture, plans the work, and scaffolds the entire project — governed by the
AI OS from the very first file.

## Dependencies

- `infra.sk` — Used for final project scaffolding and CI/CD setup
- `security.sk` — Security review of the architecture plan
- `observability.sk` — Decision logging throughout the process

## Commands

### ARCHITECT_PLAN

The primary command. Transforms an idea into a complete project plan.

```
> OS_COMMAND ARCHITECT_PLAN --idea="<your idea in plain language>"
```

Or simply describe your idea naturally — the agent will recognize the greenfield
scenario and invoke this workflow.

---

## Workflow: The 6-Phase Ideation Pipeline

### Phase 1: DISCOVER — Structured Interview

Do NOT ask all questions at once. Run 2-3 questions per round, refine, and dig deeper.

**Round 1 — The Vision**
1. "Here's my understanding of your idea: [restate it]. Is this accurate? What would you change?"
2. "Who is the primary user? What problem does this solve for them?"
3. "Is this a side project/learning exercise, or do you intend this for production/revenue?"

**Round 2 — Scope & Features**
1. "What are the 3-5 core features that make this idea work? (The MVP — what MUST exist)"
2. "What features are nice-to-have but not essential for launch?"
3. "Are there existing products that do something similar? What would you do differently?"

**Round 3 — Constraints & Preferences**
1. "Do you have a preferred tech stack, or should I recommend one?"
2. "Any hard constraints? (Budget, hosting preferences, must work offline, specific integrations)"
3. "Timeline — do you have a target date or is this open-ended?"

**Round 4 — Scale & Future**
1. "How many users do you expect initially? In 6 months? In a year?"
2. "Will you be working on this alone or with a team?"
3. "Any compliance or regulatory requirements? (GDPR, HIPAA, PCI, etc.)"

**Completion criteria** — Move to Phase 2 when you can answer:
- [ ] What is it? (one-sentence description)
- [ ] Who is it for? (target user)
- [ ] What are the MVP features? (3-5 core features)
- [ ] What is the tech preference? (or freedom to recommend)
- [ ] What is the scale expectation?
- [ ] What is the project archetype? (hobby/startup/enterprise/critical)

---

### Phase 2: DESIGN — Architecture & Tech Stack

Based on discovery, produce a **Technical Design Document**:

#### 2a. Tech Stack Recommendation

For each layer, recommend technology with rationale:

```markdown
## Recommended Tech Stack

### Frontend
- **Framework**: [recommendation] — [why]
- **Styling**: [recommendation] — [why]
- **State Management**: [recommendation] — [why]

### Backend
- **Runtime/Framework**: [recommendation] — [why]
- **API Style**: REST / GraphQL / gRPC — [why]
- **Authentication**: [recommendation] — [why]

### Data
- **Primary Database**: [recommendation] — [why]
- **Caching**: [if needed] — [why]
- **File Storage**: [if needed] — [why]

### Infrastructure
- **Hosting**: [recommendation] — [why]
- **CI/CD**: [recommendation] — [why]
- **Monitoring**: [recommendation] — [why]
```

Selection criteria (in priority order):
1. User's explicit preference (if any)
2. Project scale requirements
3. Team size and expertise
4. Community support and longevity
5. ISO 42001 compliance considerations (for enterprise/critical)

#### 2b. Architecture Design

Produce a system architecture:
- High-level component diagram (describe in text or use mermaid)
- Data flow between components
- API surface design (key endpoints/operations)
- Database schema outline (key entities and relationships)
- Authentication/authorization model
- Error handling strategy

#### 2c. Security Architecture

Reference `security_policy.md` and assess:
- Attack surface analysis for the proposed architecture
- Authentication and authorization approach
- Data protection requirements
- Dependency risk profile

**Present the full design to the user. Wait for approval before proceeding.**

---

### Phase 3: PLAN — Feature Breakdown & Milestones

Break the approved design into implementable work:

#### 3a. Feature Decomposition

For each MVP feature:
```markdown
### Feature: [Name]
- **User Story**: As a [user], I want [action] so that [benefit]
- **Acceptance Criteria**:
  - [ ] [Criterion 1]
  - [ ] [Criterion 2]
- **Components**: [which architectural components are involved]
- **Estimated Complexity**: Simple / Medium / Complex
- **Dependencies**: [other features this depends on]
```

This is the same feature/user-story/acceptance-criteria shape `core.planning.sk` uses for
an epic's `## Story` sections — greenfield decomposition here, in-project decomposition
there. One shape; don't fork it.

#### 3b. Milestone Plan

Organize features into phased milestones:

```markdown
## Milestone 1: Foundation (Week 1-2)
- [ ] Project scaffold and tooling setup
- [ ] Database schema and migrations
- [ ] Authentication system
- [ ] Core API endpoints

## Milestone 2: Core Features (Week 3-4)
- [ ] [Feature 1]
- [ ] [Feature 2]

## Milestone 3: Polish & Launch (Week 5-6)
- [ ] UI polish and responsive design
- [ ] Error handling and edge cases
- [ ] Testing and security audit
- [ ] Deployment pipeline
```

#### 3c. Risk Assessment

Identify top 3-5 risks:
```markdown
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| [risk] | Low/Med/High | Low/Med/High | [plan] |
```

**Present the plan to the user. Wait for approval before scaffolding.**

On approval, write the full plan (3a feature decomposition + 3b milestones + 3c risks) to
`memory/plans/<YYYY-MM-DD>-<project-slug>.md` with the same header block
`core.planning.sk`'s `PLAN_WRITE` step 5 defines (`Branch`, `Created`, `Status`,
`Task file:`) — one standalone dated file, not inlined into task or semantic memory. The
task file gets the one-line `Active plan:` pointer. This keeps greenfield and in-project
plans in one predictable place.

---

### Phase 4: SCAFFOLD — Generate the Project

Once the plan is approved, execute:

1. **Create directory structure** matching the approved architecture
2. **Initialize package managers** (npm init, uv init, cargo init, etc.)
3. **Generate configuration files** (tsconfig, eslint, prettier, etc.)
4. **Set up the AI OS** — the `.ai-os/` directory is already present, but:
   - Update `manifest.json` with project name and detected archetype
   - Run perception scan to populate `project_genome.json`
   - Write the architecture decisions to `memory/episodic/decisions.jsonl`
   - Seed `memory/semantic/project_knowledge.md` with the architecture overview
   - Record the tech stack rationale in `memory/semantic/patterns.json`
5. **Generate CI/CD** via `INFRA_SETUP_CI` if the plan includes it
6. **Create README.md** from the project plan
7. **Security baseline** — run `SECURITY_AUDIT --depth=quick` on scaffolded code

---

### Phase 5: SEED — Generate Starter Code

Go beyond empty scaffolding — generate working starter code:

1. **Database models/schema** from the entity design
2. **API route stubs** with proper types and error handling
3. **Authentication boilerplate** matching the chosen strategy
4. **Frontend layout** with navigation matching the feature list
5. **Test file stubs** for each component
6. **Environment configuration** (.env.example with required variables)

All generated code passes through `SECURITY_SCAN_FILE` before writing.

---

### Phase 6: HANDOFF — Ready to Build

Present the completed scaffold to the user:

```
╔══════════════════════════════════════════════════╗
║        Project Scaffolded Successfully           ║
╠══════════════════════════════════════════════════╣
║ Project:     {name}                              ║
║ Stack:       {frontend} + {backend} + {database} ║
║ Architecture: {pattern}                          ║
║ Features:    {count} planned ({MVP_count} MVP)   ║
║ Milestones:  {count} phases                      ║
║ Files:       {count} generated                   ║
║                                                  ║
║ Next steps:                                      ║
║ 1. Review generated code in your editor          ║
║ 2. > OS_COMMAND INFRA_HEALTH_CHECK               ║
║ 3. Start building Milestone 1                    ║
╚══════════════════════════════════════════════════╝
```

Log everything in the decision journal and update progress.md.

---

## Quick Start Examples

**Bare-bones idea:**
```
> OS_COMMAND ARCHITECT_PLAN --idea="A mobile app for tracking daily water intake"
```

**More detailed:**
```
> OS_COMMAND ARCHITECT_PLAN --idea="A SaaS platform where restaurants can manage reservations, with a customer-facing booking widget they embed on their website"
```

**Just talk naturally:**
```
"I have an idea for a Chrome extension that helps people manage their browser tabs
using AI to auto-group and summarize them. Can you plan and build this?"
```
The agent will recognize this as a greenfield scenario and initiate the Architect workflow.

---

## Common Mistakes

1. **Skipping the interview** — Don't jump to scaffolding. The discovery phase prevents building the wrong thing.
2. **Over-scoping MVP** — MVP means minimum. Push nice-to-haves to later milestones.
3. **Choosing tech for its novelty** — Pick boring, proven technology for the core. Experiment in non-critical areas.
