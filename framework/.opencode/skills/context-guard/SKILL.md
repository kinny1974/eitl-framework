---
name: context-guard
description: "Monitors context window usage and triggers automatic memory save + compaction when thresholds are exceeded. Designed for EitL pipeline with 128k token limit."
---

# Skill: context-guard

## Role
You are a context window guardian. Prevent context overflow by monitoring usage and automatically saving important context to memory before compacting.

## Thresholds (Designed for 128k limit)

| Level | Threshold | Action |
|-------|-----------|--------|
| OK | < 65% (0‑83k) | Continue normally |
| **WARNING** | **65‑85% (83‑109k)** | **Auto-save to memory + compact immediately** |
| **CRITICAL** | **≥ 86% (110k+)** | **Auto-save to memory + compact immediately** |

> **Why 86%?**  
> With a 128 000 token window, 86 % ≈ 110 000 tokens. This gives you a safety buffer while still preventing collapse.

## Automatic Actions on WARNING (65‑85% / 83‑109k)

When context reaches **83 000 tokens** or more (but below 110 000), execute these steps **in order**:

### 1. Save to Memory (before compaction)
`
guardar_conversacion(
  title="Context auto-save @ 100k",
  summary="[Generate concise summary of current work]",
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
- Preserve last **10 priority messages** (critical for continuity)
- Summarize older messages
- Clear resolved blockers from context

## Automatic Actions on CRITICAL (≥ 110k)

When context reaches **110 000 tokens** or more, execute these steps **in order**:

### 1. Save to Memory (before compaction)
`
guardar_conversacion(
  title="Context auto-save @ 110k",
  summary="[Generate concise summary of current work]",
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
- Preserve last **10 priority messages** (critical for continuity)
- Summarize older messages
- Clear resolved blockers from context

## What to Save Before Compaction

| Category | Tool | When |
|----------|------|------|
| Conversation summary | guardar_conversacion | Always on WARNING and CRITICAL |
| Technical decisions | guardar_decision | If any were made (WARNING or CRITICAL) |
| Task progress | guardar_tarea | If tasks are in_progress (WARNING or CRITICAL) |
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
- When standalone: save to itl-artifacts/DECISIONS.md and itl-artifacts/TASKS.md

## Agent Profiles

| Agent | Safe Threshold | Critical Threshold | Priority Messages |
|-------|---------------|-------------------|-------------------|
| scrum-master | 65% | 86% | 8 |
| product-owner | 60% | 86% | 10 |
| architect | 55% | 86% | 6 |
| tdd-engineer | 60% | 86% | 8 |
| validator | 65% | 86% | 10 |

## Rules
1. Check context before EVERY agent switch
2. On WARNING (65‑85%): auto-save to memory + compact immediately
3. On CRITICAL (≥ 110k): auto-save to memory + compact immediately
4. NEVER lose: decisions, task progress, or file changes
5. Log all compaction events for post-mortem analysis
