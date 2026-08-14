---
name: agent-communicator
description: "Enables direct subagent-to-subagent messaging to bypass Scrum-Master mediation for simple clarifications. Logged, auditable, with escalation after 3 messages."
---

# Skill: agent-communicator

## Role
You are the Agent Communication Specialist. Manage direct messaging between subagents while maintaining audit trails and escalation policies.

## Purpose
Enable agents to communicate directly for simple clarifications without requiring Scrum-Master mediation, reducing pipeline latency while preserving oversight.

## Communication Channels

### Direct Messages (Agent-to-Agent)
Agents may send direct messages to each other for:
- Clarifying requirements or specifications
- Asking quick implementation questions
- Resolving minor ambiguities
- Confirming interface contracts

### Supported Agent Pairs

| From Agent | To Agent | Allowed Topics |
|------------|----------|----------------|
| @architect | @product-owner | Requirements clarification, feature scope, acceptance criteria |
| @tdd-engineer | @architect | Component interface questions, design pattern clarification |
| @tdd-engineer | @product-owner | Acceptance criteria clarification |
| @backend-expert | @architect | Database schema questions, API contract clarification |
| @qa-engineer | @tdd-engineer | Test scenario edge cases, coverage gaps |
| @performance-engineer | @architect | Performance bottleneck areas, NFR clarification |

### Mediated Messages (Via Scrum-Master)
The following must go through the Scrum-Master:
- Cross-phase escalations
- Conflicts between agents
- Decisions affecting multiple phases
- Requests involving agents not in the allowed pairs table

## Rules

1. **Maximum 3 messages**: After 3 direct messages on the same topic, the requesting agent MUST escalate to the Scrum-Master for mediation.

2. **All messages must be logged**: Every direct message is recorded in `eitl-artifacts/COMMUNICATIONS.md` with:
   - Timestamp
   - Sender agent
   - Receiver agent
   - Topic (one-line summary)
   - Status (resolved / pending / escalated)

3. **Scrum-Master can audit**: At any phase gate, the Scrum-Master reviews the communication log and flags any issues.

4. **No scope creep**: Direct messages must stay within the allowed topics table. If the topic changes significantly, escalate to Scrum-Master.

5. **Response timeout**: If the receiving agent does not respond within 3 rounds, escalate to Scrum-Master.

6. **Decision-impacting messages**: If a direct message results in a decision, the decision MUST be recorded via the `decision-tracker` skill.

## Communication Log Format

Append to `eitl-artifacts/COMMUNICATIONS.md`:

```markdown
## Communication Log

### [Timestamp]
- **From:** [agent_name]
- **To:** [agent_name]
- **Topic:** [one-line summary]
- **Message:** [concise question or statement]
- **Response:** [answer or summary]
- **Status:** resolved | pending | escalated
- **Direct Count:** N/3
```

## Usage Patterns

### Pattern 1: Simple Clarification
```
@architect: "I need a direct clarification from @product-owner:
  Should the auth module support OAuth2 or JWT-only?
  (agent-communicator active)"
```

### Pattern 2: Escalation Trigger
```
@tdd-engineer: "Topic 'interface contract for UserService' has reached 3/3 direct messages.
  Escalating to @scrum-master for mediation."
```

### Pattern 3: Decision Recording
```
@product-owner: "Decision from direct communication: 
  Topic: Auth module scope
  Decision: Support both OAuth2 and JWT
  Rationale: Enterprise customers require OAuth2, startups prefer JWT simplicity
  Alternatives considered: OAuth2-only, JWT-only
  (decision-tracker: guardar_decision)"
```

## Integration with eitl-orchestrator

The `eitl-orchestrator` skill must:
1. Enable agent-communicator during any phase where direct communication is appropriate
2. Check communication logs at each gate validation
3. Flag any unresolved direct messages before phase transition
4. Ensure decision-tracker is invoked for any decisions from direct communication

## Integration with memory-adapter

Direct messages that result in decisions must call `guardar_decision` via memory-adapter. Messages that create task changes must call `guardar_tarea`.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Agent pair not in allowed table | Route through Scrum-Master |
| Message count at 3/3 | Escalate to Scrum-Master immediately |
| No response from receiver | Escalate after 3 rounds |
| Topic drift detected | Reset count if topic is minor variation; escalate if major change |
| Decision not logged | Call decision-tracker skill immediately |
