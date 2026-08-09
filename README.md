# EitL Framework v1.0b

> **Framework**: Engineering in the Loop (EitL) for OpenCode-AI
> **Version**: 1.0b
> **Date**: 2026-08-08
> **Pipeline**: 10 agents · 21 skills · 6 gates · Full QA

---

## Table of Contents

1. [Overview](#overview)
2. [What's New in 1.0b](#whats-new-in-10b)
3. [Installation](#installation)
4. [Project Initialization](#project-initialization)
5. [Generated Structure](#generated-structure)
6. [Pipeline Usage](#pipeline-usage)
7. [E2E Smoke Test](#e2e-smoke-test)
8. [Control Commands](#control-commands)
9. [Memory Systems](#memory-systems)
10. [Troubleshooting](#troubleshooting)
11. [Glossary](#glossary)

---

## Overview

EitL (Engineering in the Loop) is a multi-agent software engineering framework for OpenCode-AI. It orchestrates a complete development pipeline from requirement to validated deployment using 10 specialized agents:

| Agent | Phase | Output |
|-------|-------|--------|
| **scrum-master** | Orchestration | Current Project State |
| **product-owner** | Design | `01_Plan_Scrum.md` |
| **architect** | Design | `02_Architecture_SDD.md` |
| **tdd-engineer** | Design | `03_Plan_TDD.md` |
| **validator** | All Gates | Validation Reports |
| **test-runner** | QA | `04_Test_Report.md` |
| **qa-engineer** | QA | `05_QA_Report.md` |
| **performance-engineer** | QA | `06_Performance_Report.md` |
| **backend-expert** | Implementation | Backend Code |
| **spec-lead** | Architecture | Technical Specifications |

## What's New in 1.0b

- **Generic Configuration**: Project configs are generated from templates using environment-variable placeholders (`CPU_BASEURL`, `API_KEY`, etc.).
- **Memory Adapter**: Works with KinnyCode, Mem0, LanceDB-OpenCode, or standalone (no memory server).
- **Plugin Tests**: 44 unit tests + 1 stress test (45 total) for the context-guard plugin (100% statement / 100% branch / 100% line coverage with Vitest, run in shuffled order).
- **E2E Smoke Test**: `e2e/smoke-e2e.sh` validates project initialization end-to-end (structure + M8 re-init anti-regression, optional live check).
- **Standalone Mode**: Run EitL without any external memory system.
- **English**: Agent prompts and skills are in English; note that artifact templates and some plugin messages remain in Spanish.

## Installation

### Prerequisites

| Component | Minimum Version | Notes |
|-----------|----------------|-------|
| **OpenCode** | ≥ 1.4.7 | With native plugin support |
| **Node.js** | ≥ 22.6.0 | Required for plugin API |
| **Python** | ≥ 3.10 | For memory systems (optional) |
| **Git** | Any | For artifact versioning |

### Step 1: Download and Extract

```powershell
# Windows
Expand-Archive -Path "eitl-framework-v1.0b.zip" -DestinationPath "$env:USERPROFILE\Tools\eitl-framework"
```

```bash
# Linux / macOS
unzip eitl-framework-v1.0b.zip -d ~/tools/eitl-framework
```

### Step 2: Verify Structure

```
eitl-framework/
├── framework/                    ← REUSABLE (do not edit)
│   └── .opencode/
│       ├── agents/             ← 10 agents
│       ├── skills/             ← 21 skills
│       ├── plugin/             ← context-guard.ts + tests
│       ├── command/            ← TUI commands
│       └── eitl/               ← templates + initial state
├── project-config-template/
│   ├── opencode.jsonc.template ← generic config with placeholders
│   ├── tui.json.template       ← TUI config
│   └── .env.template           ← environment variables
├── init-scripts/
│   ├── init-eitl.ps1           ← Windows
│   └── init-eitl.sh            ← Linux/Mac
├── e2e/
│   └── smoke-e2e.sh            ← E2E smoke test (T-13)
├── QUICKSTART.md               ← 5-minute standalone setup
└── README.md                   ← This file
```

## Project Initialization

### Quick Start (Standalone — No Memory Server)

```powershell
# Windows
cd C:\Users\$env:USERNAME\Documents\projects
mkdir my-project; cd my-project

& "$env:USERPROFILE\Tools\eitl-framework\init-scripts\init-eitl.ps1" `
    -ProjectName "my-project" `
    -CpuBaseUrl "http://localhost:11434/v1" `
    -GpuBaseUrl "http://localhost:11434/v1" `
    -ApiKey "not-needed"
```

```bash
# Linux / macOS
mkdir -p ~/projects/my-project
cd ~/projects/my-project

export MEMORY_ENABLED=false
export CPU_BASEURL=http://localhost:11434/v1
export API_KEY=not-needed

bash ~/tools/eitl-framework/init-scripts/init-eitl.sh "my-project"
```

### With Memory Server (e.g., KinnyCode)

```powershell
& "$env:USERPROFILE\Tools\eitl-framework\init-scripts\init-eitl.ps1" `
    -ProjectName "my-project" `
    -KinnyCodePath "C:\ProgramData\KinnyCode\memory" `
    -MemoryServerUrl "http://127.0.0.1:8005" `
    -CpuBaseUrl "http://localhost:11434/v1" `
    -ApiKey "not-needed"
```

## Generated Structure

After initialization, your project has this structure:

```
my-project/
│
├── .opencode/                    ← EitL Framework (DO NOT edit manually)
│   ├── agents/                   ← 10 agent definitions
│   ├── skills/                   ← 21 skills
│   ├── plugin/                   ← context-guard.ts
│   ├── command/                  ← TUI commands
│   ├── eitl/                     ← templates + initial state
│   ├── opencode.jsonc            ← Generated project config
│   └── tui.json                  ← TUI config
│
└── eitl-artifacts/               ← PROJECT ARTIFACTS (outside .opencode)
    ├── 01_Plan_Scrum.md
    ├── 02_Architecture_SDD.md
    ├── 03_Plan_TDD.md
    ├── 04_Test_Report.md
    ├── 05_QA_Report.md
    ├── 06_Performance_Report.md
    └── CURRENT_STATE.md
```

**Golden Rule**: Everything project-specific (artifacts, state, decisions) goes in `eitl-artifacts/`. `.opencode/` is the framework — if you need to change something there, modify the framework and reinitialize.

## Pipeline Usage

### Start OpenCode

```bash
cd my-project
opencode
```

### Available Commands

| Command | Phase | Agent | Output |
|---------|-------|-------|--------|
| `/start-SDD [requirement]` | Design | product-owner → architect → tdd-engineer | `01_Plan_Scrum.md` → `02_Architecture_SDD.md` → `03_Plan_TDD.md` |
| `/start-TDD [id]` | Design (jump) | architect → tdd-engineer | `02_Architecture_SDD.md` → `03_Plan_TDD.md` |
| `/start-IMPL [id]` | Implementation | (delegate to dev) | Source code |
| `/run-tests [component]` | QA | test-runner | `04_Test_Report.md` |
| `/qa-check` | QA | qa-engineer | `05_QA_Report.md` |
| `/perf-test` | QA | performance-engineer | `06_Performance_Report.md` |
| `/regen [scrum\|sdd\|tdd]` | Control | — | Regenerates artifact |
| `/status` | Control | scrum-master | Shows current state |
| `/blocker [msg]` | Control | scrum-master | Registers blocker |
| `/context-guard check [agent]` | Control | — | Checks context |
| `/yolo on` / `/yolo off` | Control | scrum-master | Toggles autonomous mode |

### Validation Gates

| Gate | Artifact | Validator | Approval Criteria |
|------|----------|-----------|-------------------|
| **Gate 1** | `01_Plan_Scrum.md` | validator | Scrum plan checklist: verifiable stories, defined DoD, traceability |
| **Gate 2** | `02_Architecture_SDD.md` | validator | SDD checklist: ADRs, data models, API contracts, NFRs |
| **Gate 3** | `03_Plan_TDD.md` | validator | TDD plan checklist: 80/15/5 pyramid, edge cases, fixtures |
| **Gate 4** | `04_Test_Report.md` | validator | Coverage ≥ 80%, 0 failed tests |
| **Gate 5** | `05_QA_Report.md` | validator | 0 CRITICAL issues, ≤ 5 HIGH |
| **Gate 6** | `06_Performance_Report.md` | validator | All NFRs met with ≥ 10% margin |

### Context Protection

Before each agent delegation, the scrum-master automatically invokes:

```
/context-guard check [target_agent]
```

If WARNING: considers compaction. If CRITICAL: compacts or aborts.

## E2E Smoke Test

`e2e/smoke-e2e.sh` validates that the framework initializes a project correctly from scratch (T-13). It checks:

- **Structure**: 10 agents, 21 skills, `opencode.jsonc`, `tui.json`, context-guard plugin and `CURRENT_STATE.md`.
- **M8 anti-regression**: re-initialization **replaces** (does not nest) an existing `.opencode/` and creates a `.opencode-backup-<fecha>`.
- **Live smoke (optional)**: loads the plugin in a real OpenCode session (`GUARD_OK` response).

The script runs against a temporary project (`mktemp`) that is cleaned up automatically on exit, so it leaves no residue in `/tmp`.

### Running

```bash
# Structural only (CI-friendly, no LLM required)
bash e2e/smoke-e2e.sh

# + Live smoke with real OpenCode (requires the opencode CLI and a configured LLM)
OPENCODE_SMOKE=1 bash e2e/smoke-e2e.sh
```

| Exit code | Meaning |
|-----------|---------|
| `0` | PASS — all checks succeeded |
| `1` | FAIL — structural error (blocks the `e2e` CI job) |
| `2` | SKIP — live smoke not available (not a structural failure) |

> The live smoke runs `opencode run` with the `architect` agent and verifies the context-guard plugin answers `GUARD_OK`. If no LLM is configured, it prints a warning and skips — this does not fail the CI.

## Memory Systems

EitL v1.0b supports multiple memory backends via the `memory-adapter` skill:

| Backend | Type | Storage | Deployment | Notes |
|---------|------|---------|------------|-------|
| **KinnyCode** | Proprietary multilayer | LanceDB | Local | Your current stack, MCP integration |
| **Mem0** | Conversational memory | Cloud | Cloud | `npx -y mem0-mcp` |
| **LanceDB-OpenCode** | Native plugin | LanceDB | Local | OpenCode marketplace |
| **Standalone** | File-based | Markdown | None | No server required |

### Standalone Mode

If no MCP memory server is detected, EitL operates in standalone mode:
- State persists in `eitl-artifacts/CURRENT_STATE.md`
- Tasks tracked in `eitl-artifacts/TASKS.md`
- Decisions appended to `eitl-artifacts/DECISIONS.md`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `context-guard` plugin not found | Ensure `"context-guard"` is in `opencode.jsonc` plugins array |
| Artifacts not appearing | Check parent directory: `ls ../eitl-artifacts/` |
| No LLM endpoint responding | Test with `curl [CPU_BASEURL]/v1/models` |
| Memory server not connecting | Verify `MEMORY_SERVER_URL` and that the server is running |
| Standalone still tries to connect to the memory MCP | `MEMORY_ENABLED` was not set | The init scripts honor `MEMORY_ENABLED` (default `false` → `"enabled": false`); set `MEMORY_ENABLED=true` only if you have a memory server (see `doc/06`) |
| Init script fails on Windows | Ensure PowerShell execution policy allows scripts: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned` |

## Glossary

| Term | Definition |
|------|------------|
| **EitL** | Engineering in the Loop — Multi-agent software engineering pipeline |
| **SDD** | Software Design Document — Architecture specification |
| **TDD** | Test-Driven Development — Tests before code |
| **NFR** | Non-Functional Requirement — Performance, security, scalability |
| **ADR** | Architectural Decision Record — Documented technical decision |
| **Gate** | Validation checkpoint that blocks pipeline on failure |
| **YOLO Mode** | Autonomous mode that auto-approves gates without human intervention |
| **Context Guard** | Plugin that monitors LLM context window usage |
| **MCP** | Model Context Protocol — Standard for tool integration |
| **Artifact** | Generated document (markdown) produced by a pipeline phase |
