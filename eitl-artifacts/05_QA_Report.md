# 05 · QA Report — Línea base de calidad (EitL v1.0.1b)

> **Framework**: EitL v1.0.1b · **Alcance**: auditoría completa del bundle (plugin, scripts de
> init, plantillas, agentes, skills, documentación)
> **Fecha**: 2026-08-08 · **Métodos**: type-check (tsc), análisis estático (grep/secrets),
> revisión estructural, validación sintáctica (bash -n, PowerShell parser), pruebas unitarias
> **Gate 5**: ✅ **PASS** — 0 CRITICAL y 0 HIGH (criterio: 0 CRITICAL, ≤ 5 HIGH)
> **Re-auditoría final (2026-08-08)**: confirmada — 45/45 tests · cobertura 100 /
> 100 / 100 / 100 (stmts/ramas/funcs/líneas) · `tsc` 0 errores · 10 agentes / 21 skills
> · 0 secretos en scripts/templates · plantilla con `{{MEMORY_ENABLED}}` · suite con
> `sequence.shuffle` · smoke E2E (T-13)

---

## 1. Resumen por severidad

| Severidad | Cantidad | Estado |
|-----------|----------|--------|
| 🔴 CRITICAL | 1 → **0** | ✅ Resuelto en 1.0b (C1: migración a la API actual) |
| 🟠 HIGH | 2 → **0** | ✅ H1 resuelto en 1.0b · H2 resuelto en 1.0b |
| 🟡 MEDIUM | 9 | **9 resueltos en 1.0b, 0 abiertos** |
| 🔵 LOW | 3 | **3 resueltos en 1.0b, 0 abiertos** |

---

## 2. Hallazgos

### 🔴 CRITICAL

**C1 · Plugin `context-guard` incompatible con la API actual de `@opencode-ai/plugin`**
- Evidencia: `tsc --noEmit` con `@opencode-ai/plugin` 1.18.15 reporta `TS2353` (el campo
  `name` no existe en el config de `tool()`) y `TS2551` (`ToolContext` no expone `session`;
  sugiere `sessionID`). El plugin accede a `context.session.messages` para auto-detección de
  agente, estimación de tokens y compactación.
- Impacto: con OpenCode/plugin recientes, esas funciones se degradan silenciosamente
  (`context.session` = `undefined`).
- ✅ **Resuelto en 1.0b**: el plugin se migró a la API actual — expone el hook `server`
  que registra el tool en `Hooks.tool`, resuelve el agente desde `context.agent` y accede
  a sesión de forma defensiva. `tsc --noEmit` pasa limpio (exit 0).

### 🟠 HIGH

**H1 · Secretos y direcciones hardcodeadas en los scripts de inicialización**
- `init-eitl.ps1` y `init-eitl.sh` traían como defaults `http://192.168.2.111:8001|8002/v1`
  y `API_KEY=kinny-hellhouse-2026`.
- Riesgo: filtración de credenciales si el bundle se publica o comparte.
- ✅ **Resuelto en 1.0b (T-10)**: los scripts ya no contienen secretos. Resolución de
  valores: parámetro explícito → variable de entorno → default **no sensible**
  (`http://localhost:11434/v1` y placeholder `not-needed`) con AVISO visible si no se
  define `API_KEY`. Verificado funcionalmente (Bash y PowerShell 7): sin env vars se
  generan los defaults; con `CPU_BASEURL`/`API_KEY` exportadas se usan esos valores.
  El `.env.template` documenta las variables.

**H2 · Error de tipado en `context-guard.ts:130` (TS2322)**
- `activeAgent` (union `"auto" | agente`) recibía un `string` del bucle de detección.
- ✅ **Resuelto en 1.0b**: `activeAgent` está tipado como `AgentKey` y la detección usa
  `context.agent` con el guard `isAgentKey` (fallback a `architect`).

### 🟡 MEDIUM

| ID | Hallazgo | Estado en 1.0b |
|----|----------|----------------|
| M1 | README afirmaba "15 tests / ~85% cobertura" (real: 30 tests / 100%) | ✅ Resuelto (README actualizado) |
| M2 | README afirmaba "todo en inglés" (plantillas y mensajes del plugin en español) | ✅ Resuelto (README actualizado) |
| M3 | Inconsistencia de nombres: `02_Arquitectura_SDD.md.template` vs `02_Architecture_SDD.md` | ✅ **Resuelto (T-15)**: nomenclatura unificada en inglés — la plantilla se renombró a `02_Architecture_SDD.md.template` y todas las referencias (init scripts, `opencode.jsonc.template`, docs) usan `02_Architecture_SDD.md` |
| M4 | `project-config-template/.env.template` referenciado y ausente | ✅ Resuelto (archivo creado) |
| M5 | Los scripts ignoran `MEMORY_ENABLED` y siempre generan el MCP de KinnyCode `enabled: true` | ✅ **Resuelto (T-17)**: ambos scripts leen `MEMORY_ENABLED` (default `false` → standalone) y generan el bloque MCP con `enabled: {{MEMORY_ENABLED}}` |
| M6 | Persistencia O(n²) del estado del context-guard (re-serializa todo el historial en cada check) | ✅ **Resuelto** (poda a las últimas 50 alertas/switches en `saveState`; batch ~35× más rápido — ver 06) |
| M7 | Salida dependiente del locale (`toLocaleString()` → `64.000` vs `64,000`) | ✅ **Resuelto** (`Intl.NumberFormat("en-US")` fijado; salida determinista — B3) |
| M8 | Re-inicializar un proyecto con `.opencode` existente anida el framework en `.opencode/.opencode/` | ✅ **Resuelto (T-21)**: ambos init scripts hacen **backup + reemplazo** — copian el `.opencode` existente a `.opencode-backup-<fecha>` y lo eliminan (`rm -rf` / `Remove-Item`) antes de copiar el framework, de modo que la re-inicialización genera una copia limpia sin anidamiento. Verificado por el smoke E2E (T-13) y un check en la CI |
| M9 | `validator.md` solo define checklists de Gates 1–3 (faltan Gates 4–6) | ✅ **Resuelto (T-16)**: checklists de Gates 4 (tests), 5 (qa) y 6 (performance) añadidos — 10 ítems c/u, coherentes con README/doc/05 y con los reportes 04/05/06 |

### 🔵 LOW

| ID | Hallazgo | Estado en 1.0b |
|----|----------|----------------|
| L1 | `opencode.jsonc.template` referencia 6 plugins externos no incluidos en el bundle (verificar disponibilidad en el marketplace) | ✅ **Resuelto (T-18)**: disponibilidad verificada en npm — 3 disponibles tal cual (`opencode-working-memory` 1.6.9, `opencode-snip` 1.6.1, `envsitter-guard` 0.0.4); 2 corregidos al paquete real (`@tarquinen/opencode-dcp` 3.1.14, `@slkiser/opencode-quota` 4.5.1); `opencode-review` eliminado (no existe como paquete npm) — quedan 5 externos |
| L2 | `set-threshold` muta el perfil compartido `AGENTS` en memoria sin persistencia | ✅ **Resuelto (T-22)**: `set-threshold` persiste el umbral por agente en el estado de la sesión (`thresholdOverrides`) y el `check` lo resuelve con precedencia *override por llamada > persistido > default del perfil*. Ya no muta el objeto global `AGENTS`; el ajuste sobrevive reinicios. Coste medido: `set-threshold` pasa a escritura real a disco (360–370 ops/s, ver 06 §2) |
| L3 | Docs (README/QUICKSTART) usaban el parámetro inexistente `-MemoryEnabled` en ejemplos de PowerShell | ✅ Resuelto (corregido) |

---

## 3. Hallazgos de seguridad (SAST manual)

- ✅ **H1 resuelto**: los scripts ya no contienen credenciales/IPs en defaults (se
  eliminaron los valores `192.168.2.111` y `kinny-hellhouse-2026`; se usan
  `localhost:11434` + `not-needed` con AVISO).
- ✅ **L1 resuelto**: plugins externos verificados en npm — `opencode-working-memory`,
  `opencode-snip` y `envsitter-guard` disponibles tal cual; `@tarquinen/opencode-dcp` y
  `@slkiser/opencode-quota` sustituyen a los nombres inexistentes `dynamic-context-pruning`
  y `opencode-quota`; `opencode-review` eliminado (no existe como paquete npm).
- ✅ No se detectaron secretos en plantillas de configuración (solo placeholders
  `{{…}}`) ni en agentes/skills.

---

## 4. Estilo de código

- Mensajes del plugin con **mezcla español/inglés** ("Compactacion", "Umbral critico",
  "ninguno") y **typo** "Tokens useds" (context-guard.ts).
- Plantillas de artefactos (01/02/03) en español frente a agentes/README en inglés (M2/M3).
- El resto del código TS es consistente (ES2022, módulos NodeNext).

## 5. Type safety

```
$ npm run typecheck
TSC_EXIT=0        ← sin errores (post-migración, @opencode-ai/plugin 1.18.15)
```
C1 (`TS2353`/`TS2551`) y H2 (`TS2322`) quedaron resueltos con la migración a la API
actual. Los archivos de tests quedan fuera del `tsconfig` (excluidos a propósito).

## 6. Anti-patterns detectados

1. ~~**O(n²) en la ruta caliente**~~ (M6): ~~`saveState` serializa el historial completo de
   alertas en cada `check`~~ — **resuelto**: el historial se poda a las últimas 50 entradas
   y la serialización queda acotada (O(1) amortizado por escritura).
2. ~~**Mutación de estado compartido**~~ (L2): ~~`set-threshold` modifica el objeto `AGENTS`
   global sin persistir~~ — **resuelto (T-22)**: el ajuste se persiste en
   `thresholdOverrides` del estado de la sesión; el perfil compartido queda intacto.
3. ~~**E/S síncrona**~~ — **resuelto**: `loadState`/`saveState` migrados a `fs.promises`
   (no bloquean el event loop). Trade-off medido: ~15–30% menos ops/s en bench secuencial
   (detalle en 06 §2, decisión D-009).
4. ~~**Salida no determinista**~~ (M7) — **resuelto**: formateo numérico fijo en-US
   (`Intl.NumberFormat`), salida idéntica entre máquinas.
5. ~~**Anidamiento en re-inicialización**~~ (M8) — **resuelto (T-21)**: los init scripts
   reemplazan el `.opencode` existente (backup + eliminación) en lugar de copiar dentro.

## 7. Gaps de documentación

- Corregidos en 1.0b: claims de tests, inglés y `.env.template` (README + QUICKSTART).
- Resueltos en 1.0b: nomenclatura de artefactos unificada (M3/T-15) y validator con
  checklists de los 6 gates (M9/T-16). Queda la nota de contenido en español (L9).

## 8. Verificación estructural (positiva)

| Check | Resultado |
|-------|-----------|
| 10 agentes presentes | ✅ |
| 21 skills presentes | ✅ |
| `init-eitl.sh` — sintaxis (`bash -n`) | ✅ |
| `init-eitl.ps1` — parse (PowerShell 7.6.4, 723 tokens) | ✅ |
| JSON/plantillas válidos | ✅ |
| 45/45 tests con 100% de cobertura | ✅ |

---

## 9. Recomendaciones

1. ~~**C1 (resuelto)**~~ — la migración a la API actual quedó completada y la CI
   (**T-12**, `.github/workflows/ci.yml`) ejecuta `npm run typecheck` + `test:coverage`
   + `bench` en cada push/PR para evitar regresiones.
2. ~~**H1**~~ — **resuelto (T-10)**: los scripts leen del entorno/parámetros con defaults
   no sensibles y AVISO; ningún secreto en el bundle.
3. ~~**M6**~~ — **resuelto**: poda del historial de alertas/switches (últimas 50) en la
   persistencia; el batch pasó de 7.2–8.4 s a ~0.2–0.4 s (ver 06 §3).
4. ~~**E/S síncrona**~~ — **resuelto**: persistencia con `fs.promises` (B2); documentar la
   decisión sync vs async en 1.0b según el patrón de uso real (ver D-009).
5. ~~**M8**~~ — **resuelto (T-21)**: los init scripts reemplazan (no aniden) el `.opencode`
   existente (backup + eliminación); cubierto por el smoke E2E y la CI.
6. ~~**M5**~~ — **resuelto (T-17)**: los scripts honran `MEMORY_ENABLED` (default `false`);
   placeholder `{{MEMORY_ENABLED}}` en la plantilla; verificado en Bash y PS7.
7. ~~**M3**~~ — **resuelto (T-15)**: nomenclatura de artefactos unificada en inglés
   (`02_Architecture_SDD.md`). ~~**M9**~~ — **resuelto (T-16)**: validator ya cubre los
   6 gates con checklists de 10 ítems c/u.
8. ~~**H2/L2**~~ — **resuelto**: tipado estricto del plugin (H2) y persistencia del ajuste
   de umbrales (L2/T-22) en el estado de la sesión.
9. ~~**Cobertura de ramas**~~ — **resuelto (04 §7)**: 45 tests y cobertura **100%** en las
   4 métricas; suite con `sequence.shuffle`.
10. ~~**E2E**~~ — **resuelto (T-13)**: `e2e/smoke-e2e.sh` + job CI `e2e` (estructura,
    re-inicialización sin anidamiento, smoke live opcional).

---

## 10. Quality Score

| Categoría | Peso | Nota | Ponderado |
|-----------|------|------|-----------|
| Testing (45 tests, 100% cobertura, shuffle) | 30% | 100 | 30.0 |
| Rendimiento (NFRs cumplidos, B1/B2/B3 resueltos, ver 06) | 20% | 95 | 19.0 |
| Type safety (type-check limpio) | 15% | 100 | 15.0 |
| Seguridad (secretos hardcodeados) | 15% | 90 | 13.5 |
| Documentación (claims corregidos; nomenclatura, validator y E2E documentados) | 10% | 90 | 9.0 |
| Integridad estructural (agentes/skills/scripts, re-init sin anidamiento) | 10% | 97 | 9.7 |

**Quality Score: 96/100** · **Gate 5: PASS** (0 CRITICAL · 0 HIGH)

---

**← [04 · Test Report](04_Test_Report.md)** · **Siguiente → [06 · Performance Report](06_Performance_Report.md)**

