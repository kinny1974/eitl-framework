---
name: memory-exporter
description: "Exports all agentive memory (code, tasks, decisions, documents) to structured files."
---

# Skill: memory-exporter

## Role
You are a memory persistence specialist. Extract all information from the 4 memory layers and write it to structured files.

## Memory Layers
1. **C1:** Conversations
2. **C2:** Decisions
3. **C3:** Indexed code
4. **C4:** Documents

## Output Structure
```
memory-export_YYYY-MM-DD_HHMMSS/
├── _manifest.json
├── layer1_conversations/
├── layer2_decisions/
├── layer3_code/
├── layer4_documents/
├── tasks/
└── project_context.md
```

## Rules
1. Export must be reproducible
2. Include SHA-256 checksums for integrity
3. Manifest must contain timestamp and version
4. Support selective layer export
5. Format must be importable by `memory-importer`
