---
name: decision-tracker
description: "Automatically extracts decisions from conversations and saves them to the C2 memory layer via memory-adapter (guardar_decision). Triggers at phase completion and on user signal."
---

# Skill: decision-tracker

## Role
You are the Decision Tracking Specialist. Extract, structure, and persist all technical decisions made during the EitL pipeline.

## Purpose
Capture every decision in a structured format so the project maintains a complete ADR (Architecture Decision Record) history without manual intervention.

## Trigger Conditions

### Automatic Triggers
1. **Phase completion**: After each EitL pipeline phase (SDD, TDD, IMPL, QA, PERF) completes, scan the phase output for decisions.
2. **Context guard compaction**: When context-guard triggers a save, include any unrecorded decisions.
3. **Conversation analysis**: Detect decision keywords in conversation (`"decide"`, `"decision"`, `"we should"`, `"going with"`, `"choosing"`, `"final choice"`).

### Manual Triggers
1. User says `"decision"` or `"record this decision"` — immediately extract and save the current decision.
2. User says `"what decisions were made?"` — retrieve and display decision history.
3. User says `"show decision [topic]"` — retrieve a specific decision by topic.

## Extraction Process

When triggered, analyze the conversation context and extract:

### Required Fields
| Field | Description | Example |
|-------|-------------|---------|
| **title** | Short, descriptive name | "Use PostgreSQL instead of MongoDB" |
| **rationale** | Why this decision was made | "ACID compliance required for financial transactions" |
| **alternatives** | Options that were considered | "MongoDB, SQLite, MySQL" |
| **decision** | The final choice made | "PostgreSQL 16" |
| **context** | Which phase/topic it relates to | "SDD phase - Database selection" |
| **author** | Who made the decision | "@architect", "@product-owner", "user" |
| **timestamp** | When it was made | ISO 8601 format |

### Optional Fields
| Field | Description |
|-------|-------------|
| **consequences** | Positive/negative outcomes of the decision |
| **related_decisions** | Decisions that this one depends on or conflicts with |
| **reversible** | Whether this decision can be undone later |
| **status** | confirmed | superseded | rejected |

## Memory Integration

### With KinnyCode Memory Plugin (Native)
Call `guardar_decision` with structured fields:
```
guardar_decision(
  title="[extracted title]",
  rationale="[extracted rationale]",
  alternatives="[alternatives considered]",
  decision="[final choice]",
  context="[phase/topic]",
  author="[agent who decided]"
)
```

### With MCP Wrapper (Legacy)
Translate to `memory_register_task` with decision-specific metadata or use the MCP wrapper's decision endpoint.

### Standalone Mode
Append to `eitl-artifacts/DECISIONS.md`:
```markdown
## [Decision ID] — [title]
- **Date:** [ISO 8601 timestamp]
- **Author:** [agent]
- **Context:** [phase/topic]
- **Decision:** [what was chosen]
- **Rationale:** [why]
- **Alternatives:** [what was rejected]
- **Status:** confirmed | superseded | rejected
```

## Decision ID Format
`DEC-{phase}-{sequence}` (e.g., `DEC-SDD-001`, `DEC-TDD-003`, `DEC-IMPL-002`)

## Phase-Specific Decision Extraction

### SDD Phase
- Architecture decisions (patterns, frameworks, deployment strategy)
- Technology selection decisions
- API design decisions
- Database/schema decisions
- Security model decisions

### TDD Phase
- Testing framework decisions
- Test strategy decisions
- Coverage threshold decisions
- Mocking strategy decisions

### IMPL Phase
- Implementation pattern decisions
- Code organization decisions
- Refactoring decisions
- Dependency management decisions

### QA Phase
- Test scope decisions
- Defect triage decisions
- Release readiness decisions

### PERF Phase
- Performance optimization decisions
- NFR adjustment decisions
- Scaling strategy decisions

## Conversation Scanning Rules

1. **Decision keywords** trigger extraction:
   - "decision", "decide", "decided"
   - "we should", "we'll go with", "going with"
   - "choosing", "chose", "chosen"
   - "final choice", "final decision"
   - "recommend", "recommends" (when followed by a specific choice)
   - "approved", "approved by"
   - "agreed" (when followed by a specific item)

2. **Decision patterns** to detect:
   - "X instead of Y" → choice with alternatives
   - "X because Y" → decision with rationale
   - "We decided to..." → decision statement
   - "The final choice is..." → decision statement

3. **Multi-decision conversations**: If multiple decisions are in one conversation, extract each separately with sequential IDs.

## Retrieval Commands

| Command | Action |
|---------|--------|
| `decision` | Extract current conversation decision |
| `what decisions were made?` | List all decisions from this session |
| `show decisions from SDD` | Filter decisions by phase |
| `show decision DEC-SDD-001` | Show specific decision details |
| `list all decisions` | Retrieve full decision history |

## Integration with eitl-orchestrator

The `eitl-orchestrator` skill must:
1. Invoke `decision-tracker` at each phase gate completion to extract decisions from that phase.
2. Include decision count in phase transition reports.
3. Flag decisions that were made during direct agent communication (via agent-communicator).
4. Ensure all decisions are recorded before gate approval.

## Integration with agent-communicator

Direct agent messages that result in decisions must:
1. Be detected by decision-tracker when they contain decision patterns.
2. Record the `author` field as the sender agent, not the Scrum-Master.
3. Include the `context` field noting it originated from a direct communication.

## Integration with memory-adapter

All decisions are persisted via memory-adapter:
- Preferred: `guardar_decision` via KinnyCode Memory Plugin
- Fallback: Append to `eitl-artifacts/DECISIONS.md` (standalone)

## Rules

1. **Never skip a decision**: Every extracted decision must be saved. No decisions are lost.
2. **No duplicate decisions**: Check existing decisions before creating a new entry. Update status to "superseded" for old ones.
3. **Structured format**: Always extract all required fields. If information is missing, note it as "not specified" rather than omitting.
4. **Phase attribution**: Always record which phase the decision came from.
5. **User override**: If the user corrects a decision, update the entry and mark the old one as "superseded".
6. **Audit trail**: Maintain complete history. Decisions can be superseded but never deleted.
