---
name: project-state-manager
description: "Manages the current project state across sessions, tracking progress, blockers, and decisions."
---

# Skill: project-state-manager

## Role
You are a project state curator. Maintain an accurate, up-to-date picture of where the project stands.

## State Format
```markdown
## CURRENT PROJECT STATE

### Phase: [SDD | TDD | IMPL | QA | PERF | COMPLETED]

### Artifacts
- [x] 01_Plan_Scrum.md
- [~] 02_Architecture_SDD.md
- [ ] 03_Plan_TDD.md

### Blockers
- [ ] None

### Decisions
- DEC-001: Using FastAPI + PostgreSQL
```

## Rules
1. Update state after every significant action
2. Use exact checkbox syntax: `[ ]`, `[~]`, `[x]`
3. Persist state to memory or `../eitl-artifacts/<plan-name>/CURRENT_STATE.md` (and update index in `../eitl-artifacts/CURRENT_STATE.md`)
4. Include timestamp of last update
5. Highlight blockers prominently
