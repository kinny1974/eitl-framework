# 04 · Test Report — Línea base de QA (EitL v1.0b)

> **Framework**: EitL v1.0b · **Componente auditado**: plugin `context-guard` + entorno de pruebas
> **Fecha**: 2026-08-08 · **Herramienta**: Vitest 4.1.10 (Node v24.11.1 · Windows)
> **Gate 4**: ✅ **PASS** — cobertura ≥ 80% y 0 tests fallidos

---

## 1. Resumen

| Métrica | Valor | Criterio Gate 4 | Estado |
|---------|-------|------------------|--------|
| Tests totales | **45** | — | — |
| Tests pasados | **45** | — | ✅ |
| Tests fallidos | **0** | 0 fallos | ✅ |
| Tests saltados | 0 | — | ✅ |
| Cobertura de sentencias | **100%** | ≥ 80% | ✅ |
| Cobertura de ramas | **100%** | ≥ 80% | ✅ |
| Cobertura de funciones | **100%** | ≥ 80% | ✅ |
| Cobertura de líneas | **100%** | ≥ 80% | ✅ |
| Duración total de la suite | ~2–6 s (según carga de la máquina) | — | ✅ |

> El criterio del framework es cobertura general ≥ 80% (métrica principal: líneas);
> ramas/funciones se reportan como referencia.

> **Actualización (sugerencias implementadas)**: la suite creció de 36 a **45 tests**
> (44 unit + 1 estrés) y la cobertura llegó a **100% en las 4 métricas** — se cubrieron
> las ramas restantes (formatReport sin historial, `loadState` con archivo corrupto,
> fallbacks de límite, `sessionID` ausente, dry-run sin `messages`) y se eliminó una
> rama muerta (`?? 0` tras el guard `hasLive`). Además la suite ahora se ejecuta con
> **`sequence.shuffle`** (04 §7.4) para garantizar la independencia de los tests.

**Veredicto Gate 4**: APROBADO.

---

## 2. Resultados de tests unitarios (`__tests__/context-guard.test.ts` — 44 tests)

Los tests importan y ejecutan el **plugin real** (no reimplementan su lógica). El API de
`@opencode-ai/plugin` y `fs`/`path` están mockeados; el estado se persiste en memoria.
La suite se ejecuta con **orden aleatorio** (`sequence.shuffle` en `vitest.config.ts`,
04 §7.4) para demostrar que los tests son independientes (cada uno crea/limpia su
propio estado). Nota: los tests usan la **ToolContext de la API actual** (`agent`,
`directory`, `worktree`) con acceso defensivo a la fuente legacy de sesión.

| Suite | Tests | Resultado |
|-------|-------|-----------|
| Contrato del módulo (tool config, sin `name`, hook `server`, defaults, rangos) | 7 | ✅ 7/7 |
| Detección de agente (`context.agent` / explícito / fallbacks) | 4 | ✅ 4/4 |
| Niveles de alerta (OK 50% · WARNING 65% · CRITICAL 85% · override · umbral exacto `>=`) | 5 | ✅ 5/5 |
| Cálculo de tokens (live · persistido · no disponibles · límite por modelo · restantes · fallbacks de límite) | 7 | ✅ 7/7 |
| Persistencia de estado (corrupto → default · acumulación · lastTokenUsage · poda a 50 alertas · poda a 50 switches) | 5 | ✅ 5/5 |
| Acción `switch-agent` | 1 | ✅ 1/1 |
| Acción `report` (historial · últimas alertas · vacío → `(none)`/`(ninguno)`) | 3 | ✅ 3/3 |
| Acción `set-threshold` (error sin override · persistencia en estado · sin mutar AGENTS · check posterior respeta el persistido) | 4 | ✅ 4/4 |
| Acción `compact` (dry-run · dry-run sin messages · legacy · sin soporte nativo · errores) | 5 | ✅ 5/5 |
| Pipeline hints (pistas EitL por agente) | 1 | ✅ 1/1 |
| Ramas restantes (sin OPENCODE_STATE_DIR · sin sessionID → `unknown`) | 2 | ✅ 2/2 |

### Test de estrés / métricas de memoria (`__tests__/perf-batch.test.ts` — 1 test)

| Métrica | Resultado (post-poda) |
|---------|------------------------|
| 2,000 checks en lote | **0.30 – 0.49 s** (~4,230–6,640 ops/s) — antes 7.2–21.9 s |
| Δ RSS | **3.6 – 3.7 MB** — antes 30.3 – 42.3 MB |
| Δ heapUsed | **0.8 – 0.9 MB** — antes 2.0 – 23.4 MB |
| Sanity (elapsed < 60 s) | ✅ |

> ℹ️ **Re-corrida de las sugerencias (2026-08-08)**: tras la iteración L2, el batch
> registró 301–494 ms / Δ RSS 3.6–3.7 MB. Los rangos consolidados incluyen las corridas
> de la línea base (0.21–0.24 s / 5.2–5.6 MB) — el detalle por columna está en
> [06 §3](06_Performance_Report.md).

---

## 3. Cobertura por componente

| Archivo | % Stmts | % Branch | % Funcs | % Lines | Líneas sin cubrir |
|---------|---------|----------|---------|---------|-------------------|
| `plugin/context-guard.ts` | **100** | **100** | **100** | **100** | — |

Cobertura total: se añadieron tests para las ramas que quedaban (historial vacío de
`formatReport`, `loadState` con JSON corrupto, fallbacks de `DEFAULT_LIMIT`, `sessionID`
ausente, dry-run sin `messages`) y se eliminó la rama muerta `?? 0` (el guard `hasLive`
ya garantiza que `total` es numérico).

---

## 4. Tests de integración y E2E

- **Integración**: N/A en esta auditoría (el plugin se valida de forma unitaria con mocks
  de la API de OpenCode). El plugin **typecheckea limpio** contra la API actual
  (`@opencode-ai/plugin` 1.18.15) — el hallazgo C1 del reporte 05 quedó resuelto con la
  migración.
- **E2E del pipeline** (inicialización + plugin): **implementado (T-13)** —
  `e2e/smoke-e2e.sh` inicializa un proyecto temporal, valida la estructura completa y
  **re-inicializa comprobando que no anida** `.opencode/.opencode/` (M8). Con
  `OPENCODE_SMOKE=1` (y CLI `opencode` + LLM real) ejecuta además un smoke live que
  fuerza la carga del plugin `context-guard` en sesión real. El flujo completo
  SDD → TDD → QA → PERF con agentes reales queda como línea de trabajo de las
  próximas iteraciones de 1.0b.

---

## 5. Detalle de tests fallidos

**0 fallidos.** Nota de auditoría: la suite original del bundle (7 tests) reimplementaba la
lógica del plugin inline (no lo importaba) y arrojaba **cobertura real 0%**. Fue reemplazada
por la suite actual (45 tests, 100% de cobertura en las 4 métricas). El README ya refleja
los números reales.

---

## 6. Logs de ejecución (resumen verificado)

```
$ npm run typecheck        # exit 0
RUN  v4.1.10 — seed "0" (sequence.shuffle activo)
✓ __tests__/context-guard.test.ts (44 tests)
[PERF] 2,000 checks en 301–494 ms → 4,230–6,640 ops/s | RSS Δ: 3.6–3.7 MB | heapUsed Δ: 0.8–0.9 MB
✓ __tests__/perf-batch.test.ts (1 test)
Test Files  2 passed (2)
     Tests  45 passed (45)

% Coverage report from v8
File              | % Stmts | % Branch | % Funcs | % Lines
 context-guard.ts |    100 |     100 |     100 |     100
```

---

## 7. Recomendaciones

1. ~~**CI**~~ — **resuelto (T-12)**: `.github/workflows/ci.yml` ejecuta `npm run
   typecheck`, `test:coverage` (con thresholds ≥ 80%) y `bench` en cada push/PR;
   `vitest.config.ts` ahora falla si la cobertura baja del 80%.
2. ~~**Cubrir ramas restantes**~~ — **resuelto**: la cobertura llega a **100% en las 4
   métricas** (45 tests) — historial vacío de `formatReport`, `loadState` corrupto,
   fallbacks de límite, `sessionID` ausente y dry-run sin `messages` ya tienen test.
3. ~~**E2E del pipeline**~~ — **resuelto (T-13)**: `e2e/smoke-e2e.sh` inicializa un
   proyecto temporal, verifica la estructura (10 agentes / 21 skills / configs),
   **re-inicializa verificando que no anida** (M8) y ofrece smoke live con OpenCode
   real (`OPENCODE_SMOKE=1`). Job `e2e` en la CI.
4. ~~**Aislamiento**~~ — **resuelto**: `vitest.config.ts` activa `sequence.shuffle`
   (orden aleatorio con seed fijo `0`); los tests pasan en cualquier orden porque cada
   uno limpia/crea su propio estado.

---

**Siguiente → [05 · QA Report](05_QA_Report.md)**
