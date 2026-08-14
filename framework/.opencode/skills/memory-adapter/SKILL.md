---
name: memory-adapter
description: "Generic memory abstraction layer for EitL. Compatible with KinnyCode Memory Plugin (native TypeScript), Mem0, LanceDB-OpenCode, or standalone mode."
---

# Skill: memory-adapter
# Framework: OpenCode-AI EitL — Memory Abstraction

## Purpose
This skill provides a unified interface for agentive memory operations, decoupling the EitL pipeline from any specific memory implementation.

## Design Principle
> **Convention over Configuration**: The skill auto-detects the available memory backend and routes operations to the correct implementation.

## Memory Backend Priority

1. **KinnyCode Memory Plugin** (Native TypeScript) — Recommended
   - Plugin: `opencode-kinnycode-memory`
   - 18 native tools for indexing, search, conversations, tasks, and memory management
   - No Python dependencies, integrated in OpenCode
   - Best performance and maintainability

2. **KinnyCode MCP Wrapper** (Legacy Python)
   - Requires Python + httpx + mcp
   - Two codebases to maintain
   - Consider migrating to native plugin

3. **Mem0** — Conversational memory with entity extraction
   - Cloud-based, `npx -y mem0-mcp`

4. **LanceDB-OpenCode** — Native OpenCode plugin with LanceDB
   - Local storage, OpenCode marketplace

5. **Standalone** — File-based (no memory server)
   - All state persists in markdown files inside `eitl-artifacts/`

## Unified Memory API

### With KinnyCode Memory Plugin (Native)

When the plugin `opencode-kinnycode-memory` is configured, use these tools directly:

#### Indexing (4 tools)
- `indexar_archivo` — Index a code file
- `indexar_proyecto` — Index multiple files
- `indexar_documento` — Index PDF/MD/TXT document
- `reindexar_archivo` — Re-index if hash changed

#### Search (3 tools)
- `buscar_codigo` — Semantic search in code
- `buscar_documentos` — Search in documents
- `recuperar_contexto` — Full RAG (all layers)

#### Document Management (2 tools)
- `listar_documentos` — List indexed documents
- `eliminar_documento` — Delete a document

#### Conversations & Decisions (3 tools)
- `guardar_conversacion` — Save conversation history
- `cargar_conversacion` — Retrieve conversation history
- `guardar_decision` — Save technical decision

#### Tasks (2 tools)
- `guardar_tarea` — Create/update a task (L5)
- `buscar_tareas` — Semantic search in tasks

#### Memory Management (3 tools)
- `consolidar_memoria` — Consolidate memory (remove obsolete)
- `contexto_sesion` — Proactive session context
- `limpiar_proyecto` — Delete all project data

### Automatic Consolidation Triggers (Phase-Based)

The EitL pipeline triggers `consolidar_memoria` after each mandatory phase:

| Phase | Trigger | Tool Call |
|-------|---------|-----------|
| After `/start-SDD` + Gate 1 | Scrum Plan approved | `consolidar_memoria(filter_type="phase-complete")` |
| After Gate 2 (SDD) | Architecture approved | `consolidar_memoria(filter_type="architecture")` |
| After Gate 3 (TDD) | TDD Plan approved | `consolidar_memoria(filter_type="tdd")` |
| After `/start-IMPL` | Implementation done | `consolidar_memoria(filter_type="implementation")` |
| After `/run-tests` + Gate 4 | Tests passed | `consolidar_memoria(filter_type="tests")` |
| After `/qa-check` + Gate 5 | QA approved | `consolidar_memoria(filter_type="qa")` |
| After `/perf-test` + Gate 6 | Performance NFRs met | `consolidar_memoria(filter_type="performance")` |

**Rationale**: After each gate, obsolete intermediate decisions and stale task entries are cleaned up to reduce context pressure. The consolidated memory keeps only:
- Approved artifacts references
- Final architectural decisions
- Current task status
- Session summary (if context > 60%)

#### Consolidation Parameters

```
consolidar_memoria(
  project_id="6b6a8b869aea48ad",
  filter_type="phase-complete",  # "architecture" | "tdd" | "tests" | "qa" | "performance" | "phase-complete"
  keep_recent=true,               # Keep last N entries per layer
  remove_obsolete=true            # Remove entries marked as superseded
)
```

#### Project (1 tool)
- `info_proyecto` — Project statistics

### With MCP Wrapper (Legacy)

All operations use the `memory_` prefix and are translated to the detected backend:

#### Save Project State
```
memory_save_state(project_id, state_object)
```

#### Load Project State
```
memory_load_state(project_id)
```

#### Register Task
```
memory_register_task(task_id, title, description, status, priority, dependencies)
```

#### Search Memory
```
memory_search(query, n_results, filter_type)
```

#### Export Memory
```
memory_export(output_dir, layers)
```

#### Import Memory
```
memory_import(import_dir, mode)
```

### Standalone Mode (No Memory Server)

If no memory backend is detected, the pipeline operates in **standalone mode**:

- All state persists in markdown files inside `eitl-artifacts/`
- Tasks are tracked in `eitl-artifacts/TASKS.md`
- Decisions are appended to `eitl-artifacts/DECISIONS.md`
- Cross-session context is recovered by reading these files at startup

## Configuration

### Option 1: KinnyCode Memory Plugin (Recommended)

Add to `opencode.jsonc`:

```jsonc
{
  "plugin": [
    ["opencode-kinnycode-memory", {
      "serverUrl": "http://192.168.2.111:8007",
      "projectId": "6b6a8b869aea48ad"
    }]
  ]
}
```

Or using environment variables:

```powershell
$env:KINNYCODE_SERVER_URL = "http://192.168.2.111:8007"
$env:KINNYCODE_PROJECT_ID = "6b6a8b869aea48ad"
```

Then in `opencode.jsonc`:

```jsonc
{
  "plugin": ["opencode-kinnycode-memory"]
}
```

### Option 2: MCP Wrapper (Legacy)

```jsonc
{
  "mcp": {
    "memory": {
      "type": "local",
      "command": ["{{MEMORY_PYTHON_PATH}}", "{{MEMORY_WRAPPER_PATH}}"],
      "environment": {
        "MEMORY_SERVER_URL": "{{MEMORY_SERVER_URL}}",
        "PROJECT_ID": "{{PROJECT_ID}}"
      },
      "enabled": {{MEMORY_ENABLED}}
    }
  }
}
```

### Option 3: Standalone (No Memory Server)

Set `MEMORY_ENABLED=false` in `.env` or leave memory configuration empty.

## EitL Pipeline Integration

### Automatic State Persistence

The EitL pipeline automatically saves:

1. **Project State** → `eitl-artifacts/CURRENT_STATE.md` (standalone) or KinnyCode memory
2. **Tasks** → `eitl-artifacts/TASKS.md` (standalone) or KinnyCode tasks layer
3. **Decisions** → `eitl-artifacts/DECISIONS.md` (standalone) or KinnyCode decisions layer

### Cross-Session Recovery

When starting a new session:

1. If KinnyCode plugin is configured: `recuperar_contexto` retrieves all relevant context
2. If standalone: Read `eitl-artifacts/CURRENT_STATE.md` to restore project state

### Phase-Based Memory Consolidation (Pipeline Integration)

The ScrumMaster triggers automatic consolidation after each pipeline phase. This reduces context pressure and keeps memory lean:

```
# After each gate approval (automated by scrum-master):
consolidar_memoria(filter_type="phase-complete")

# Before heavy delegations (auto by context-guard):
guardar_conversacion() + guardar_tarea()  # saves state before compaction
context_guard_check() → if CRITICAL → compact → then continue
```

**Consolidation benefit**: After consolidation, memory footprint reduces by ~30-50%, freeing context for new pipeline phases. The `consolidar_memoria` tool removes:
- Superseded intermediate decisions
- Resolved task entries (automatically archived)
- Stale conversation fragments (before the current active phase)

### Agent Memory Operations

Agents can use memory operations directly:

```
# Index current project files
indexar_proyecto(project_path=".", language="typescript")

# Search for architectural decisions
recuperar_contexto(prompt="What architectural decisions were made?")

# Save a technical decision
guardar_decision(title="Use PostgreSQL", rationale="ACID compliance required")

# Post-phase consolidation (called by ScrumMaster)
consolidar_memoria(filter_type="phase-complete")
```

## Migration from MCP Wrapper to Native Plugin

To migrate from the MCP wrapper to the native KinnyCodeMemory plugin:

1. **Install the plugin**:
   ```bash
   cd F:\kinnyCodeMemory\plugin-kinnycode
   npm install
   npm run build
   ```

2. **Update opencode.jsonc**:
   - Remove the `mcp.kinnycode-memory` section
   - Add `"opencode-kinnycode-memory"` to the `plugin` array

3. **Update environment variables**:
   - Replace `MEMORY_SERVER_URL` with `KINNYCODE_SERVER_URL`
   - Replace `PROJECT_ID` with `KINNYCODE_PROJECT_ID`

4. **Test the integration**:
   - Start OpenCode: `opencode`
   - Verify plugin loaded: `/mcp`
   - Test a tool: `info_proyecto`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Plugin not found | Ensure `opencode-kinnycode-memory` is installed and built |
| Server connection failed | Verify server is running: `ssh hell-house "systemctl status kinnycodememory"` |
| Project ID not found | Check available projects: `curl -X POST http://192.168.2.111:8007/project-info -H "Content-Type: application/json" -d '{"project_id": "..."}'` |
| Tools not appearing | Restart OpenCode after adding plugin to config |
