# EitL Framework v1.0.1b

> **Framework**: Engineering in the Loop (EitL) for OpenCode-AI
> **Version**: 1.0.1b
> **Date**: 2026-08-09
> **Pipeline**: 10 agents · 21 skills · 6 gates · Full QA

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Project Initialization](#project-initialization)
4. [Memory Configuration](#memory-configuration)
5. [Generated Structure](#generated-structure)
6. [Pipeline Usage](#pipeline-usage)
7. [Troubleshooting](#troubleshooting)
8. [Documentation](#documentation)

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

---

## Installation

### Prerequisites

| Component | Minimum Version | Notes |
|-----------|----------------|-------|
| **OpenCode** | >= 1.4.7 | With native plugin support |
| **Git** | Any | For version control |

### Step 1: Clone the Repository

```bash
git clone https://github.com/kinny1974/eitl-framework.git
cd eitl-framework
```

### Step 2: Plugins

EitL configures plugins in `opencode.jsonc`. When you start OpenCode, it reads the config and installs/loads the plugins automatically.

| Plugin | Purpose | When Installed |
|--------|---------|----------------|
| `context-guard` | Context monitoring | Always (included in EitL) |

#### Memory Plugins (Optional)

If you choose memory mode in the init script, one of these plugins is configured:

| Plugin | Server | Storage |
|--------|--------|---------|
| `opencode-kinnycode-memory` | KinnyCodeMemory | LanceDB (server) |
| `mem0` | Mem0 | Cloud |
| `lancedb-opencode-pro` | LanceDB-OpenCode | LanceDB (local) |

---

## Project Initialization

### Step 1: Run the Init Script

```powershell
# Windows
cd F:\eitl-framework\init-scripts
.\init-eitl.ps1
```

```bash
# Linux / macOS
cd ~/eitl-framework/init-scripts
./init-eitl.sh
```

The script will ask:
1. Project name
2. Memory mode (standalone / with server)
3. Plugin type (KinnyCodeMemory, Mem0, LanceDB)
4. Server URL (if using memory)
5. Project ID (if using KinnyCodeMemory)

### Step 2: Start OpenCode

```bash
cd ../my-project
opencode
```

OpenCode reads `opencode.jsonc` and installs the configured plugins automatically.

### Parametrized Mode

```powershell
# Windows - Standalone
.\init-eitl.ps1 -ProjectName "my-project" -MemoryMode standalone

# Windows - KinnyCodeMemory (new project)
.\init-eitl.ps1 -ProjectName "my-project" -MemoryMode local -MemoryPlugin kinnycode -MemoryUrl "http://localhost:8007"

# Windows - KinnyCodeMemory (existing project with ID)
.\init-eitl.ps1 -ProjectName "my-project" -MemoryMode local -MemoryPlugin kinnycode -MemoryUrl "http://localhost:8007" -ProjectId "abc123def456"

# Windows - Mem0
.\init-eitl.ps1 -ProjectName "my-project" -MemoryMode local -MemoryPlugin mem0 -MemoryUrl "http://localhost:8003"

# Windows - LanceDB
.\init-eitl.ps1 -ProjectName "my-project" -MemoryMode local -MemoryPlugin lancedb
```

```bash
# Linux - Standalone
./init-eitl.sh "my-project" standalone

# Linux - KinnyCodeMemory (new project)
./init-eitl.sh "my-project" local kinnycode "http://localhost:8007"

# Linux - KinnyCodeMemory (existing project with ID)
./init-eitl.sh "my-project" local kinnycode "http://localhost:8007" "abc123def456"

# Linux - Mem0
./init-eitl.sh "my-project" local mem0 "http://localhost:8003"

# Linux - LanceDB
./init-eitl.sh "my-project" local lancedb
```

---

## Memory Configuration

### Standalone Mode (Default)

No memory server. State is saved in `eitl-artifacts/`:
- `CURRENT_STATE.md` -- Project state
- `TASKS.md` -- Task tracking
- `DECISIONS.md` -- Decision log

### Supported Memory Plugins

| Plugin | Type | Storage | URL Default |
|--------|------|---------|-------------|
| **kinnycode** | KinnyCodeMemory | LanceDB (server) | http://localhost:8007 |
| **mem0** | Mem0 | Cloud | http://localhost:8003 |
| **lancedb** | LanceDB-OpenCode | LanceDB (local) | http://localhost:8007 |

### Recommended: KinnyCodeMemory

[KinnyCodeMemory](https://github.com/kinny1974/kinnyCodeMemory) is a semantic memory server designed for EitL.

**Features:**
- Semantic search across code and documents
- Conversation history and decision tracking
- Task management with L5 priority system
- Memory consolidation and cleanup
- 18 native tools for full memory control

**Install KinnyCodeMemory:**

Option A: Download prebuilt binary
1. Go to: https://github.com/kinny1974/kinnyCodeMemory/releases
2. Download for your platform (Windows/Linux)
3. Run the server:
   ```bash
   # Windows
   .\KinnyCodeMemory-Server.exe

   # Linux
   ./KinnyCodeMemory-Server
   ```

Option B: Run from source
```bash
git clone https://github.com/kinny1974/kinnyCodeMemory.git
cd kinnyCodeMemory
pip install -r requirements.txt
python memory_server.py
```

### Alternative Memory Options

| Plugin | Type | Storage | Best For |
|--------|------|---------|----------|
| `lancedb-opencode-pro` | Vector | Local LanceDB | Local semantic search without server |
| `opencode-mem` | Vector | Local SQLite | Simple local memory |
| `opencode-working-memory` | Session | Local files | Session context only |

---

## Generated Structure

After initialization:

```
my-project/
|
|-- .opencode/                    <- EitL Framework (DO NOT edit)
|   |-- agents/                   <- 10 agent definitions
|   |-- skills/                   <- 21 skills
|   |-- plugin/                   <- context-guard.ts
|   |-- opencode.jsonc            <- Generated config (includes plugin refs)
|   +-- tui.json                  <- TUI config
|
+-- eitl-artifacts/               <- PROJECT ARTIFACTS
    |-- CURRENT_STATE.md
    |-- 01_Plan_Scrum.md
    |-- 02_Architecture_SDD.md
    |-- 03_Plan_TDD.md
    |-- 04_Test_Report.md
    |-- 05_QA_Report.md
    +-- 06_Performance_Report.md
```

---

## Pipeline Usage

### Start OpenCode

```bash
cd my-project
opencode
```

### Available Commands

| Command | Phase | Output |
|---------|-------|--------|
| `/start-SDD [requirement]` | Design | Full design pipeline |
| `/start-TDD [id]` | Design (jump) | Architecture + TDD |
| `/start-IMPL [id]` | Implementation | Source code |
| `/run-tests [component]` | QA | `04_Test_Report.md` |
| `/qa-check` | QA | `05_QA_Report.md` |
| `/perf-test` | QA | `06_Performance_Report.md` |
| `/status` | Control | Current state |
| `/blocker [msg]` | Control | Register blocker |
| `/yolo on` | Control | Autonomous mode (no pauses) |
| `/yolo off` | Control | Disable autonomous mode |

### Quick Mode (for experiments)

```bash
# 1. Enable YOLO
/yolo on

# 2. Run only what you need
/start-SDD [requirement]
/start-IMPL [id]
/run-tests

# 3. Skip gates you don't need
# Simply don't run /qa-check or /perf-test
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Script fails on Windows | Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned` |
| Memory server not connecting | Check if server is running and URL is correct |
| Artifacts not appearing | Check `../eitl-artifacts/` (parent directory) |
| No LLM responding | Configure your model provider in OpenCode settings |
| Plugin not found | Restart OpenCode to auto-install plugins |

---

## Documentation

| Document | Description |
|----------|-------------|
| [00 - Glossary](doc/00-glossario.md) | Terms and definitions |
| [01 - Installation](doc/01-instalacion.md) | Prerequisites and setup |
| [02 - New Project](doc/02-inicializar-proyecto-nuevo.md) | Initialize from scratch |
| [03 - Existing Project](doc/03-inicializar-proyecto-existente.md) | Add EitL to existing code |
| [04 - Memory](doc/04-memoria.md) | Memory plugins and configuration |
| [05 - Pipeline](doc/05-pipeline-y-comandos.md) | Commands and workflow |
| [06 - Troubleshooting](doc/06-solucion-de-problemas.md) | Common issues and solutions |
| [07 - QA](doc/07-qa.md) | Quality assurance |
| [08 - Teams](doc/08-equipos.md) | Memory configuration for teams |

---

## Links

- **Repository**: https://github.com/kinny1974/eitl-framework
- **KinnyCodeMemory**: https://github.com/kinny1974/kinnyCodeMemory
- **OpenCode**: https://opencode.ai
