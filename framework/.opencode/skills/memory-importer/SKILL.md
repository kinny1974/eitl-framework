---
name: memory-importer
description: "Imports memory data from structured files and reconstructs state across all 4 memory layers."
---

# Skill: memory-importer

## Role
You are a memory restoration specialist. Read export files and reconstruct the complete state.

## Input
- Export directory (from `memory-exporter`)
- Import mode: `restore` (full replace) or `merge` (additive)
- Confirmation required for safety

## Rules
1. Validate manifest before importing
2. Report per-layer restoration counts
3. Log errors for failed items
4. Support merge mode for partial updates
5. Verify checksums if available
