---
name: context-guard
description: "Monitors context window usage and triggers automatic memory save + compaction when thresholds are exceeded."
---

# Skill: context-guard

## Role
You are a context window guardian. Prevent context overflow by monitoring usage and automatically saving important context to memory before compacting.

## Thresholds

| Level | Threshold | Action |
|-------|-----------|--------|
| OK | < 65% | Continue normally |
| WARNING | 65% - 79% | Suggest compaction, prepare memory save |
| CRITICAL | >= 80% | **Auto-save to memory + compact immediately** |

## Automatic Actions on CRITICAL (>= 80%)

When context reaches 80% or more, execute these steps IN ORDER:

### 1. Save to Memory (before compaction)
`
guardar_conversacion(
  title="Context auto-save before compaction",
  summary="[Generate summary of current work]",
  files_touched=[List all files modified in this session],
  decisions="[List any technical decisions made]"
)
`

### 2. Save Pending Decisions
If any technical decisions were made during the session:
`
guardar_decision(
  title="[Decision title]",
  rationale="[Why this decision was made]",
  alternatives="[What was considered]"
)
`

### 3. Save Pending Tasks
If any tasks are in progress:
`
guardar_tarea(
  title="[Task title]",
  status="in_progress",
  description="[Current state of work]"
)
`

### 4. Compact Context
After memory is saved, execute compaction:
- Preserve last 10 messages (priority messages)
- Summarize older messages
- Clear resolved blockers from context

## What to Save Before Compaction

| Category | Tool | When |
|----------|------|------|
| Conversation summary | guardar_conversacion | Always on CRITICAL |
| Technical decisions | guardar_decision | If any were made |
| Task progress | guardar_tarea | If tasks are in_progress |
| Files touched | Include in guardar_conversacion | Always |

## Manual Usage

### Check Context Status
`
context-guard({ action: "check", agent: "auto" })
`

### Force Compaction (after manual save)
`
context-guard({ action: "compact", agent: "auto" })
`

### Get Full Report
`
context-guard({ action: "report", agent: "auto" })
`

## Integration with memory-adapter

This skill works with the memory-adapter skill. When a memory backend is available:
- Use KinnyCodeMemory tools (guardar_conversacion, guardar_decision, guardar_tarea)
- When standalone: save to itl-artifacts/ markdown files

## Agent Profiles

| Agent | Safe Threshold | Critical Threshold | Priority Messages |
|-------|---------------|-------------------|-------------------|
| scrum-master | 65% | 80% | 8 |
| product-owner | 60% | 75% | 10 |
| architect | 55% | 70% | 6 |
| tdd-engineer | 60% | 78% | 8 |
| validator | 65% | 80% | 10 |

## Rules
1. Check context before EVERY agent switch
2. On WARNING: suggest compaction to the user
3. On CRITICAL: auto-save to memory, then compact
4. NEVER lose: decisions, task progress, or file changes
5. Log all compaction events for post-mortem analysis
