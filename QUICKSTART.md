# EitL Quick Start — Standalone Mode (No Memory Server Required)

> Get the EitL pipeline running in under 5 minutes without any external memory system.

---

## Prerequisites

| Component | Minimum Version | Notes |
|-----------|----------------|-------|
| **OpenCode** | >= 1.4.7 | With native plugin support |
| **Node.js** | >= 22.6.0 | Required for plugin API |
| **Git** | Any | For artifact versioning |

**Optional but recommended:**
- A local LLM endpoint (llama.cpp, ollama, vLLM, or any OpenAI-compatible API)
- If you don\'t have one, EitL works with remote APIs (OpenAI, Anthropic, etc.)

---

## Step 1: Install the Framework

### Windows (PowerShell)
```powershell
Expand-Archive -Path "eitl-framework-v3.1.zip" -DestinationPath "$env:USERPROFILE\Tools\eitl-framework"
```

### Linux / macOS (Bash)
```bash
unzip eitl-framework-v3.1.zip -d ~/tools/eitl-framework
```

---

## Step 2: Create Your First Project

Create a `.env` file:

```bash
PROJECT_NAME=my-first-eitl-project
CPU_BASEURL=http://localhost:11434/v1
GPU_BASEURL=http://localhost:11434/v1
API_KEY=not-needed
MEMORY_ENABLED=false
```

Then initialize:

```powershell
# Windows
mkdir my-first-eitl-project; cd my-first-eitl-project
$env:MEMORY_ENABLED="false"
& "$env:USERPROFILE\Tools\eitl-framework\init-scripts\init-eitl.ps1" -ProjectName "my-first-eitl-project" -MemoryEnabled $false
```

```bash
# Linux/macOS
mkdir -p ~/projects/my-first-eitl-project
cd ~/projects/my-first-eitl-project
export MEMORY_ENABLED=false
bash ~/tools/eitl-framework/init-scripts/init-eitl.sh "my-first-eitl-project"
```

---

## Step 3: Run the Pipeline

```bash
cd my-first-eitl-project
opencode
```

In the TUI:
```
/start-SDD "Build a REST API for a todo list app with user authentication"
```

The pipeline will:
1. **Product Owner** generates `01_Plan_Scrum.md`
2. **Validator** checks Gate 1
3. **Architect** generates `02_Architecture_SDD.md`
4. **Validator** checks Gate 2
5. **TDD Engineer** generates `03_Plan_TDD.md`
6. **Validator** checks Gate 3

All artifacts are saved in `../eitl-artifacts/`.

---

## Feature Comparison

| Feature | Standalone | With Memory Server |
|---------|-----------|-------------------|
| SDD->TDD->IMPL Pipeline | Yes | Yes |
| Artifact Generation | Yes | Yes |
| Context Guard Plugin | Yes | Yes |
| Gate Validation | Yes | Yes |
| State Persistence | Yes (files) | Yes (MCP + files) |
| Cross-Session Memory | No | Yes |
| Task Tracking | Yes (markdown) | Yes (structured) |
| Decision History | Yes (markdown) | Yes (searchable) |

---

## Upgrading to Full Memory

When ready, add any MCP-compatible memory server and set `MEMORY_ENABLED=true`.
