---
name: memory-adapter
description: "Generic MCP abstraction layer for memory systems. Compatible with KinnyCode, Mem0, LanceDB-OpenCode, or any MCP memory server."
---

# Skill: memory-adapter
# Framework: OpenCode-AI EitL — Memory Abstraction

## Purpose
This skill provides a unified interface for agentive memory operations, decoupling the EitL pipeline from any specific memory implementation.

## Design Principle
> **Convention over Configuration**: If an MCP server named `memory` (or `kinnycode-memory`, `mem0`, `lancedb-memory`) exists, this skill auto-detects it and routes operations to the correct backend.

## Auto-Detection Priority

1. `kinnycode-memory` — Proprietary multilayer system (LanceDB)
2. `mem0` — Conversational memory with entity extraction
3. `lancedb-opencode` — Native OpenCode plugin with LanceDB
4. `memory` — Generic standard MCP server

## Unified Memory API

All operations use the `memory_` prefix and are translated to the detected backend:

### 1. Save Project State
```
memory_save_state(project_id, state_object)
```

### 2. Load Project State
```
memory_load_state(project_id)
```

### 3. Register Task
```
memory_register_task(task_id, title, description, status, priority, dependencies)
```

### 4. Search Memory
```
memory_search(query, n_results, filter_type)
```

### 5. Export Memory
```
memory_export(output_dir, layers)
```

### 6. Import Memory
```
memory_import(import_dir, mode)
```

## Standalone Mode (No Memory Server)

If no MCP memory backend is detected, the pipeline operates in **standalone mode**:

- All state persists in markdown files inside `eitl-artifacts/`
- Tasks are tracked in `eitl-artifacts/TASKS.md`
- Decisions are appended to `eitl-artifacts/DECISIONS.md`
- Cross-session context is recovered by reading these files at startup

## Configuration in opencode.jsonc

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
