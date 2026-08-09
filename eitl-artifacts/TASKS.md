# TASKS.md — Registro de tareas (modo standalone)

> Estados: `[ ]` Pending · `[~]` In Progress · `[x]` Completed · `[!]` Blocked
> Actualizado: 2026-08-08 · Sprint 0 (Auditoría y línea base QA v1.0b)

## Auditoría y QA

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| T-01 | Auditar estructura del framework (10 agentes, 21 skills, 6 gates, templates) | [x] | Verificado (agentes y skills correctos) |
| T-02 | Ejecutar pruebas unitarias con cobertura | [x] | 45/45 tests · 100% stmts/ramas/funcs/lines (sugerencias 04 §7) |
| T-03 | Ejecutar benchmarks de rendimiento | [x] | 2 corridas post-L2 · check 160–327 ops/s · report 1,596–1,684 · set-threshold 360–370 |
| T-04 | Migrar `context-guard` a la API actual de `@opencode-ai/plugin` | [x] | tsc exit 0 · Gate 5 PASS (C1/H2 resueltos) |
| T-05 | Generar reportes 04/05/06 (línea base QA) | [x] | `eitl-artifacts/` |
| T-06 | Crear manual de uso detallado (`doc/`) | [x] | 7 capítulos · enlaces internos validados |
| T-07 | Actualizar versión del framework a 1.0b | [x] | README, QUICKSTART, doc/, plantillas, INIT_STATE |
| T-08 | Corregir claims del README (tests, inglés, `.env.template`) | [x] | `.env.template` creado; QUICKSTART corregido |
| T-09 | Completar estructura `eitl-artifacts/` (CURRENT_STATE, TASKS, DECISIONS) | [x] | Este sprint |

## Mejoras pendientes (1.0b)

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| T-10 | Resolver HIGH H1: secretos hardcodeados en `init-eitl.ps1`/`.sh` | [x] | ✅ Defaults no sensibles (`localhost:11434` + `not-needed`) con AVISO; env vars/parámetros verificados en Bash y PS7 |
| T-11 | Conectar SDK client para métricas de sesión en vivo del guard | [ ] | `input.client` → `GET /session/{id}` + `/session/{id}/message` |
| T-12 | Definir CI (typecheck + coverage + bench) | [x] | ✅ `.github/workflows/ci.yml` (4 jobs) + thresholds de cobertura ≥ 80% + package.json versionado |
| T-13 | E2E del pipeline con OpenCode real | [x] | ✅ `e2e/smoke-e2e.sh` (estructura + re-init sin anidamiento + smoke live opcional `OPENCODE_SMOKE=1`) + job CI `e2e` |
| T-14 | Optimizar persistencia O(n²) del guard | [x] | ✅ Podada `alertsSent`/`agentSwitches` a 50 → batch ~0.2–0.4 s · M6/B1 resuelto |
| T-15 | Unificar nomenclatura de artefactos (M3) | [x] | ✅ Template renombrado a `02_Architecture_SDD.md.template`; init scripts, opencode.jsonc y docs alineados |
| T-16 | Completar checklists de Gates 4–6 en `validator.md` (M9) | [x] | ✅ Gates 4 (tests), 5 (qa) y 6 (performance) — 10 ítems c/u; input ampliado a `tests|qa|performance` |
| T-17 | Hacer que los init scripts lean `MEMORY_ENABLED` (M5) | [x] | ✅ `{{MEMORY_ENABLED}}` en plantilla; default `false` → standalone; verificado Bash/PS7 |
| T-18 | Verificar plugins externos referenciados en `opencode.jsonc.template` (L1) | [x] | ✅ Verificados en npm: 3 OK (working-memory 1.6.9, snip 1.6.1, envsitter-guard 0.0.4); 2 corregidos (@tarquinen/opencode-dcp, @slkiser/opencode-quota); opencode-review eliminado (inexistente) |
| T-19 | Migrar E/S del guard a `fs.promises` (B2, no-bloqueo del event loop) | [x] | ✅ `loadState`/`saveState` async; trade-off medido en 06 (D-009) |
| T-20 | Salida determinista del guard (B3/M7): `Intl.NumberFormat("en-US")` fijo | [x] | ✅ `formatTokens` para toda la salida numérica; tests con formato exacto |
| T-21 | Re-inicialización reemplaza (no anida) `.opencode` (M8) | [x] | ✅ Backup + `rm -rf`/`Remove-Item` antes de copiar; verificado por smoke E2E + check CI |
| T-22 | Persistir umbrales de `set-threshold` (L2) | [x] | ✅ `thresholdOverrides` en el estado; precedencia override > persistido > default; bench re-medido (360–370 ops/s) |
| T-23 | Cobertura de ramas al 100% + `sequence.shuffle` (04 §7) | [x] | ✅ 45 tests · 100% stmts/ramas/funcs/lines · orden aleatorio (seed 0) |

## Registro de actividad reciente

- 2026-08-08 · Sugerencias implementadas: M8/T-21 (init scripts reemplazan `.opencode` sin anidar), L2/T-22 (`set-threshold` persiste el umbral en el estado), cobertura de ramas al 100% (45 tests, 4 métricas), `sequence.shuffle` activo y E2E smoke test T-13 (`e2e/smoke-e2e.sh` + job CI `e2e`). Quality Score 94 → 96/100; reportes 04/05/06, doc/03, doc/06 (L3 y L10), doc/07, CURRENT_STATE y DECISIONS (D-018) actualizados.
- 2026-08-08 · T-18 completada: plugins externos verificados en npm — 3 disponibles tal cual, 2 renombrados al paquete real (`@tarquinen/opencode-dcp`, `@slkiser/opencode-quota`), `opencode-review` eliminado (no existe como paquete npm). L1 resuelto; plantillas opencode.jsonc y tui.json corregidas; check anti-regresión añadido a la CI.
- 2026-08-08 · T-16 completada: checklists de Gates 4–6 añadidos a `validator.md` (10 ítems c/u, tipos `tests|qa|performance` en el Input). M9 resuelto.
- 2026-08-08 · T-15 completada: nomenclatura unificada (M3) — template `02_Arquitectura_SDD.md.template` renombrado a `02_Architecture_SDD.md.template`; referencias en init scripts, `opencode.jsonc.template` y docs actualizadas; check anti-regresión añadido a la CI.

- 2026-08-08 · Re-auditoría final 1.0b completada: 36/36 tests, cobertura 99.03/91.46/100/100, tsc 0 errores, estructura 10 agentes/21 skills, 0 secretos, plantilla con `{{MEMORY_ENABLED}}`; batch 0.21–0.52 s con varianza por carga de máquina documentada en 04/06 y doc/07.

- 2026-08-08 · T-17 completada: init scripts leen `MEMORY_ENABLED` (default `false` → standalone; `true` → MCP habilitado). M5 resuelto.
- 2026-08-08 · T-12 completada: CI definida (GitHub Actions — plugin + bundle + PowerShell), thresholds de cobertura ≥ 80% en vitest.config.ts, `package.json`/lock versionados (quitados del .gitignore).
- 2026-08-08 · T-10 completada: H1 resuelto — sin secretos en los init scripts (defaults `localhost:11434` + `not-needed` con AVISO; env vars verificadas). Gate 5: 0 CRITICAL · 0 HIGH. Quality Score 86 → 94/100.
- 2026-08-08 · T-20 completada: salida determinista (B3/M7) — `Intl.NumberFormat("en-US")` fijo; Performance Score 93 → 95/100.
- 2026-08-08 · T-19 completada: E/S asíncrona (`fs.promises`) en `loadState`/`saveState` — sin bloqueo del event loop; trade-off medido (~15–30% menos ops/s en bench secuencial) documentado en 06 y D-009.
- 2026-08-08 · T-14 completada: poda de historial a 50 en `saveState` — batch 7.2–8.4 s → ~0.2–0.4 s, p99 check 6.9–12.1 → 4.9–6.1 ms (fs.promises). Reporte 06 actualizado.
- 2026-08-08 · T-04 completada: migración del plugin (tsc limpio, 36/36 tests).
- 2026-08-08 · T-08 completada: `.env.template` creado y claims del README corregidos.
- 2026-08-08 · T-06 completada: manual de uso en `doc/` (1,180 líneas).
- 2026-08-08 · T-02/T-03/T-05 completadas: línea base QA (reportes 04/05/06).
