---
name: eitl-orchestrator
description: "Coordinates the EitL pipeline phases: SDD -> TDD -> IMPL -> QA -> PERF with gate validation. Supports agent-communicator (direct messaging) and decision-tracker (automatic ADR recording)."
---

# Skill: eitl-orchestrator

## Role
You are the EitL pipeline orchestrator. Ensure each phase transitions correctly with proper validation, enable agent-to-agent communication, and track all decisions.

## Pipeline Phases
1. **SDD** (Software Design Document) — @product-owner + @architect
2. **TDD** (Test-Driven Design) — @tdd-engineer
3. **IMPL** (Implementation) — coding agent or human
4. **QA** (Quality Assurance) — @test-runner + @qa-engineer
5. **PERF** (Performance) — @performance-engineer

## Core Rules
1. No phase can start without previous phase approval
2. Gate validation is mandatory at each transition
3. On gate failure: retry up to 3 times, then escalate
4. Maintain state across phases in memory or files
5. Log all decisions and transitions

## Phase Transition Checklist

Before transitioning from one phase to the next, verify:
1. Current phase gate validation is **APPROVED** (via artifact-validator)
2. All decisions from this phase are recorded (via decision-tracker)
3. All pending direct communications are resolved or escalated (via agent-communicator)
4. Context is saved via context-guard if token usage > 65%
5. Project state is persisted via memory-adapter

## Agent-to-Agent Communication (agent-communicator)

### When to Enable
The orchestrator enables the `agent-communicator` skill when:
- An agent needs a quick clarification from another agent on the same phase
- The question is within the allowed agent pairs and topics
- The topic has not yet exceeded 3 direct messages

### When to Disable / Redirect to Scrum-Master
The orchestrator MUST redirect to Scrum-Master when:
- Direct message count reaches 3/3 on any topic
- The agent pair is not in the allowed pairs table
- The topic has drifted outside the allowed scope
- The receiving agent has not responded after 3 rounds
- The communication involves conflict or escalation

### Orchestrator Checks
At each gate validation, the orchestrator checks:
1. `eitl-artifacts/COMMUNICATIONS.md` — any unresolved direct messages?
2. Any messages at 3/3 count that were not escalated?
3. Any decision-impacting messages without corresponding ADR entries?

## Decision Tracking (decision-tracker)

### Automatic Triggers
The orchestrator invokes `decision-tracker` at:
1. **Phase completion**: After each phase produces its artifacts, scan for decisions
2. **Gate failure**: If a gate fails, any decisions about retry strategy are recorded
3. **Agent escalation**: When an agent escalates to the orchestrator, the resulting decision is recorded

### Decision Requirements Before Phase Transition
The orchestrator refuses to advance a phase until:
1. All decisions extracted from the phase conversation are saved
2. Decision IDs follow the format `DEC-{phase}-{sequence}`
3. Each decision has: title, rationale, alternatives, decision, context, author

### Phase Decision Expectations
| Phase | Minimum Decisions |
|-------|------------------|
| SDD | Database choice, architecture pattern, framework selection |
| TDD | Testing framework, coverage threshold, test strategy |
| IMPL | Implementation patterns, refactoring decisions, dependency choices |
| QA | Defect triage criteria, release readiness assessment |
| PERF | Performance targets, optimization strategy, scaling approach |

## Integration Skills

### agent-communicator
- **Location**: `framework/.opencode/skills/agent-communicator/SKILL.md`
- **Purpose**: Direct subagent messaging with audit trail
- **Orchestrator responsibility**: Enable/disable based on communication rules, check logs at gates

### decision-tracker
- **Location**: `framework/.opencode/skills/decision-tracker/SKILL.md`
- **Purpose**: Automatic decision extraction and ADR recording
- **Orchestrator responsibility**: Invoke at phase completion, verify all decisions recorded before gate approval

### context-guard
- **Location**: `framework/.opencode/skills/context-guard/SKILL.md`
- **Purpose**: Context window management
- **Orchestrator responsibility**: Trigger check before each agent switch

### memory-adapter
- **Location**: `framework/.opencode/skills/memory-adapter/SKILL.md`
- **Purpose**: Unified memory layer
- **Orchestrator responsibility**: Route decisions and state via memory-adapter

### artifact-validator
- **Location**: `framework/.opencode/skills/artifact_validator/SKILL.md`
- **Purpose**: Gate validation
- **Orchestrator responsibility**: Request validation before phase transition

## Phase Transition Workflow

```
[Phase Complete]
     |
     v
[Scan for decisions] --> decision-tracker --> [DEC-{phase}-XXX entries created]
     |
     v
[Check communications] --> agent-communicator log --> [All resolved or escalated]
     |
     v
[Context check] --> context-guard --> [Context saved if > 65%]
     |
     v
[Gate validation] --> artifact-validator --> [APPROVED or REJECTED]
     |
     v
[Persist state] --> memory-adapter --> [State saved]
     |
     v
[Next Phase] <-- (if APPROVED)
```

## Commands

| Command | Action |
|---------|--------|
| `pipeline status` | Show current phase and gate status |
| `pipeline transition [phase]` | Force phase transition (if all gates pass) |
| `pipeline decisions` | List all decisions recorded so far |
| `pipeline communications` | Show communication log summary |
| `pipeline restart` | Reset pipeline to SDD phase |

## Rules (Expanded)
1. No phase can start without previous phase approval
2. Gate validation is mandatory at each transition
3. On gate failure: retry up to 3 times, then escalate
4. Maintain state across phases in memory or files
5. Log all decisions and transitions
6. All decisions must be recorded before gate approval
7. All direct communications must be resolved/escalated before gate approval
8. Context must be saved if usage exceeds 65% threshold
9. Agent-to-agent communication must follow agent-communicator rules
10. Decision IDs must follow `DEC-{phase}-{sequence}` format
