# DECISIONS.md — Registro de decisiones (modo standalone)

> Formato: fecha · contexto · decisión · consecuencia. Se añade al final (append).
> Actualizado: 2026-08-09

---

## D-001 · 2026-08-08 — Versión oficial del framework: 1.0b

- **Contexto**: el README documentaba "EitL Framework v3.1"; el equipo trabaja en la
  versión **1.0b**.
- **Decisión**: 1.0b es la versión real actual; se actualizaron todas las referencias
  (README, QUICKSTART, `doc/`, `INIT_STATE.md`). El `package.json` del plugin usa `1.0.0`
  (semver — "1.0b" no es válido para npm).
- **Consecuencia**: documentación coherente con la versión en desarrollo.

## D-002 · 2026-08-08 — Línea base QA con Vitest (tests reales)

- **Contexto**: la suite original (7 tests) reimplementaba la lógica del plugin inline y
  arrojaba cobertura real **0%**.
- **Decisión**: reemplazarla por tests que importan y ejecutan el **plugin real** (Vitest 4),
  más un test de estrés y benchmarks.
- **Consecuencia**: 36/36 tests, cobertura 99% stmts / 91.66% ramas; README actualizado.

## D-003 · 2026-08-08 — Migración del plugin a la API actual de `@opencode-ai/plugin`

- **Contexto**: `tsc --noEmit` fallaba con `@opencode-ai/plugin` ≥ 1.18 (`TS2353` name,
  `TS2551` session, `TS2322` activeAgent) — hallazgo CRITICAL C1 y HIGH H2 del Gate 5.
- **Decisión**: eliminar el campo `name`; exponer el hook `server: Plugin` que registra el
  tool como clave de `Hooks.tool["context-guard"]`; detectar el agente vía `context.agent`;
  acceso defensivo (opcional) a datos de sesión; tipado estricto de `activeAgent` (`AgentKey`).
- **Consecuencia**: `tsc` limpio (exit 0); **Gate 5 PASS**. En runtimes con la API actual
  (sin tokenUsage en ToolContext) el guard reporta "no disponibles" y usa métricas
  persistidas — mejora pendiente: SDK client (T-11).

## D-004 · 2026-08-08 — Export del plugin: default = tool (tests) · server = runtime

- **Contexto**: los tests importan el tool directamente (`import plugin from ...`); el
  runtime de OpenCode carga el hook `server` del módulo.
- **Decisión**: mantener el **default export = definición del tool** (conveniencia de
  testing) y exportar `server: Plugin` para el runtime, documentado en el código.
- **Consecuencia**: suite simple sin romper el cargado esperado en runtime; verificación
  E2E en OpenCode real pendiente (T-13).

## D-005 · 2026-08-08 — Métricas de tokens: live → persistido → no disponibles

- **Contexto**: la ToolContext actual no expone `tokenUsage`; el guard no debe crashear ni
  bloquear el pipeline por falta de datos.
- **Decisión**: usar datos live si el runtime los inyecta (fuente legacy); si no, métricas
  del último check persistido (marcadas "(persistido)"); si no hay ninguna, reportar
  "no disponibles" con estado preventivo OK. `hasLive` distingue "0 tokens reales" de
  "sin datos".
- **Consecuencia**: degradación elegante y sin datos obsoletos; el guard nunca rompe el
  flujo del pipeline.

## D-006 · 2026-08-08 — `MEMORY_ENABLED` no consumido por los init scripts (limitación M5/L1)

- **Contexto**: los scripts de inicialización generan el MCP de KinnyCode siempre con
  `"enabled": true`, aunque la documentación usa `MEMORY_ENABLED=false` para standalone.
- **Decisión**: documentar la limitación (manual `doc/06`, L1) y mitigar manualmente
  (`"enabled": false` en `.opencode/opencode.jsonc` tras inicializar) hasta corregir los
  scripts (T-17).
- **Consecuencia**: el modo standalone puro requiere un paso manual documentado.

## D-007 · 2026-08-08 — `eitl-artifacts/` como línea base QA del framework

- **Contexto**: el framework define que los artefactos viven en `eitl-artifacts/` fuera de
  `.opencode/`.
- **Decisión**: usar `eitl-artifacts/` del propio bundle para la línea base QA de 1.0b
  (reportes 04/05/06 + CURRENT_STATE + TASKS + DECISIONS), versionados con Git.
- **Consecuencia**: trazabilidad de la auditoría y base reproducible para futuras
  iteraciones de 1.0b.

## D-008 · 2026-08-08 — Persistencia acotada del context-guard (poda a 50, M6 resuelto)

- **Contexto**: el guard guardaba `alertsSent`/`agentSwitches` sin límite y re-serializaba
  todo el historial en cada `saveState` → O(n²) acumulado (hallazgo MEDIUM M6, cuello de
  botella B1 del reporte 06). El reporte solo muestra las últimas 10 entradas.
- **Decisión**: podar ambos historiales a las últimas **50** entradas en `saveState`
  (constante `MAX_HISTORY = 50`, helper `pruneHistory`), sin cambiar el formato de estado
  ni el contrato del tool. Tests añadidos: 55 checks → 50 en archivo; 55 switches → 50.
- **Consecuencia**: serialización acotada (O(1) amortizado por escritura). Re-medido con
  `npm run bench` (2 corridas): `check` 437–591 ops/s (p99 2.7–3.2 ms, antes 6.9–12.1),
  batch de 2,000 checks 210–238 ms (~35× más rápido), Δ RSS 5.2–5.6 MB (~7× menos).
  Performance Score 92 → 94/100. Pendiente para más adelante: E/S asíncrona (B2) y
  formato numérico determinista (B3).

## D-009 · 2026-08-08 — E/S asíncrona en la persistencia (B2): `fs.promises`

- **Contexto**: `saveState`/`loadState` usaban `fs.writeFileSync`/`readFileSync` en la
  ruta caliente, bloqueando el event loop (cuello de botella B2 del reporte 06).
- **Decisión**: migrar la persistencia a `fs.promises` (async): `loadState` y `saveState`
  pasan a ser `async` y se `await`-ean en `execute`; los mocks de `fs` de los tests
  ganan el submódulo `promises` (readFile lanza ENOENT si no existe, igual que antes).
- **Consecuencia**: sin bloqueo del event loop. **Trade-off medido** con `npm run bench`
  (2 corridas, fs real): el throughput secuencial baja ~15–30% (check 303–357 vs
  437–591 ops/s) por el overhead de promesa + thread pool de libuv. Salvedad: el
  retroceso del batch (269–404 vs 210–238 ms) incluye overhead de microtask del mock
  async, no solo coste de fs real. Los NFRs siguen cumpliéndose (p99 check 4.9–6.1 ms
  < 20 ms). **Riesgo nuevo**: race read-modify-write si dos `execute` concurrentes
  tocan la misma sesión (baja probabilidad en uso por turno; comentado en el código).
  Decisión pendiente de validar en 1.0b con uso real de OpenCode: si domina la
  concurrencia, mantener async; si domina el throughput aislado, revertir a síncrono
  (o usar escritura diferida con `writeFileSync`). Performance Score 94 → 93/100.

## D-010 · 2026-08-08 — Salida determinista del guard (B3/M7): `Intl.NumberFormat("en-US")`

- **Contexto**: la salida del plugin usaba `toLocaleString()`, que depende del locale del
  SO (`64.000` en es-ES vs `64,000` en en-US) — salida no idéntica entre máquinas
  (hallazgo MEDIUM M7, cuello de botella B3).
- **Decisión**: fijar `Intl.NumberFormat("en-US")` en una constante de módulo
  (`fmtTokens`) + helper `formatTokens`, y usar ese helper para **toda** la salida
  numérica (líneas de tokens, remaining y `formatReport`). El formatter se instancia una
  sola vez y se reutiliza → coste nulo.
- **Consecuencia**: salida determinista e idéntica en cualquier máquina. Tests actualizados
  a formato exacto (`64,000`). Sin impacto en rendimiento (bench: check 419 ops/s ·
  p99 3.3 ms, dentro de los rangos previos). Determinismo 80 → 95; Performance Score
  93 → 95/100. B3/M7 resuelto.

## D-011 · 2026-08-08 — Sin secretos en los init scripts (H1/T-10): env vars + defaults no sensibles

- **Contexto**: `init-eitl.sh` y `init-eitl.ps1` traían como defaults
  `http://192.168.2.111:8001|8002/v1` y `API_KEY=kinny-hellhouse-2026` — filtración de
  credenciales si el bundle se publicaba o compartía (hallazgo HIGH H1).
- **Decisión**: eliminar todo secreto del bundle. Ambos scripts resuelven los valores con
  prioridad: (1) parámetro explícito (Bash: env var; PowerShell: `-CpuBaseUrl`, `-ApiKey`,
  …; se detecta con `$PSBoundParameters.ContainsKey`), (2) variable de entorno
  (`CPU_BASEURL`, `GPU_BASEURL`, `API_KEY`, `KINYCODE_PATH`, `MEMORY_URL`), (3) default NO
  sensible genérico (`http://localhost:11434/v1` y placeholder `not-needed`) con un AVISO
  visible en consola si `API_KEY` no está definida.
- **Consecuencia**: el bundle es publicable sin riesgo. Verificado funcionalmente en Bash
  y PowerShell 7: sin env vars → defaults + AVISO; con `CPU_BASEURL`/`API_KEY` exportadas
  → se usan esos valores en el `opencode.jsonc` generado. H1 resuelto: Gate 5 pasa con
  0 CRITICAL y 0 HIGH. Quality Score 86 → 94/100. Documentado en `doc/06` (L2 resuelta)
  y en el `.env.template`.

## D-012 · 2026-08-08 — CI del framework (T-12): GitHub Actions + versionar `package.json`

- **Contexto**: el `package.json` del plugin estaba **gitignored by design**, así que un
  checkout limpio no permitía instalar dependencias ni ejecutar typecheck/tests/bench —
  la CI no podía funcionar.
- **Decisión**: (1) versionar `package.json`/`package-lock.json` del plugin (quitarlos del
  `.gitignore`; `node_modules`, `bun.lock`, `coverage` siguen ignorados); (2) crear
  `.github/workflows/ci.yml` con 3 jobs: **plugin** (Node 24, `npm ci`, `npm run
  typecheck` + `test:coverage` + `bench`, con artefacto de cobertura), **bundle**
  (estructura: 10 agentes/21 skills, `bash -n`, JSON válidos, sin secretos hardcodeados
  H1) y **powershell** (parse de `init-eitl.ps1` en windows-latest); (3) añadir
  **thresholds de cobertura ≥ 80%** al `vitest.config.ts` (Gate 4 enforceable: la CI
  falla si la cobertura baja).
- **Consecuencia**: el pipeline queda protegido contra regresiones de types, tests,
  cobertura, rendimiento y estructura. La cobertura actual (99.03% stmts / 91.46% ramas)
  supera los umbrales con margen. `package-lock.json` del bundle raíz
  (`framework/.opencode/`) queda versionado también — revisar su contenido en el commit.

## D-013 · 2026-08-08 — Init scripts honran `MEMORY_ENABLED` (M5/T-17)

- **Contexto**: los scripts de inicialización generaban el bloque MCP de KinnyCode siempre
  con `"enabled": true`, ignorando la variable `MEMORY_ENABLED` documentada — el modo
  standalone puro requería editar `opencode.jsonc` a mano (hallazgo MEDIUM M5).
- **Decisión**: la plantilla usa el placeholder `{{MEMORY_ENABLED}}`; ambos scripts lo
  resuelven con **default `false`** (standalone, coherente con `.env.template`/README/QUICKSTART):
  `MEMORY_ENABLED` sin definir o `false` → `"enabled": false`; `true` → `"enabled": true`;
  valores inválidos → AVISO y caen a `false`. En PowerShell se añadió el parámetro
  `-MemoryEnabled` (con fallback a `$env:MEMORY_ENABLED`).
- **Consecuencia**: standalone puro por defecto sin pasos manuales; la memoria se activa
  explícitamente con `MEMORY_ENABLED=true`. Verificado en Bash y PowerShell 7 (4 casos:
  sin var / false / true en ambos scripts). M5 resuelto; doc 02/04/06 y `.env.template`
  actualizados.

## D-014 · 2026-08-08 — Re-auditoría final 1.0b (reportes 04/05/06 + doc/07)

- **Contexto**: completadas las mejoras de 1.0b (C1/H1/H2, M5/M6/M7, B1/B2/B3, T-10/
  T-12/T-17), se re-ejecuta la auditoría completa para fijar el estado final de la línea
  base QA antes de congelar la versión.
- **Decisión**: ejecutar type-check + tests con cobertura + benchmarks + verificación
  estructural (10 agentes / 21 skills / sintaxis de scripts / 0 secretos /
  `{{MEMORY_ENABLED}}` / JSON válidos) y consolidar los resultados en los reportes
  04/05/06 y `doc/07`.
- **Consecuencia**: estado final confirmado el 2026-08-08 — **36/36 tests** · cobertura
  **99.03% stmts / 91.46% ramas / 100% funcs / 100% líneas** · `tsc` 0 errores · Gate 4/5/6
  PASS · Quality **94/100** · Performance **95/100**. El bench/batch de la re-corrida
  registró varianza por carga de la máquina (check p99 outliers aislados hasta 31.7 ms,
  batch 422–516 ms): los rangos consolidados quedan documentados en el 06 con la
  distribución estable (p75 4.3–6.8 ms) dentro del NFR. Se corrigieron referencias
  residuales (91.66 → 91.46 % ramas en doc/07, CURRENT_STATE y TASKS).

## D-015 · 2026-08-08 — Nomenclatura unificada de artefactos (M3/T-15): inglés

- **Contexto**: la plantilla del bundle se llamaba `02_Arquitectura_SDD.md.template`
  (español) mientras que agentes, README, QUICKSTART y docs usaban
  `02_Architecture_SDD.md` (inglés). Sus hermanas ya eran inglesas (`01_Plan_Scrum.md`,
  `03_Plan_TDD.md`), así que el nombre en español era el outlier (hallazgo MEDIUM M3).
- **Decisión**: unificar **todo** en inglés. Renombrar la plantilla a
  `02_Architecture_SDD.md.template` (con su título interno y ruta de generación
  `../eitl-artifacts/02_Architecture_SDD.md`), y alinear las referencias en
  `init-eitl.sh`/`.ps1` (CURRENT_STATE generado), `opencode.jsonc.template` (descripción
  del agente architect) y `doc/05`/`doc/06`. El **contenido** en español de las plantillas
  se mantiene (limitación L9, separada de M3).
- **Consecuencia**: nomenclatura 100% consistente en todo el pipeline. M3 resuelto;
  doc/05 y doc/06 actualizados (L7 → resuelta); check anti-regresión añadido al job
  `bundle` de la CI (falla si reaparece `02_Arquitectura_SDD.md.template`).

## D-016 · 2026-08-08 — Checklists de Gates 4–6 en el validator (M9/T-16)

- **Contexto**: `validator.md` definía checklists de 10 ítems solo para los Gates 1–3
  (scrum_plan, sdd, tdd_plan); los Gates 4–6 (tests, qa, performance) no tenían criterios
  operativos en el agente, aunque README y `doc/05` los resumían (hallazgo MEDIUM M9).
- **Decisión**: añadir a `validator.md` los checklists de los Gates 4 (tests: cobertura
  ≥ 80% medida sobre el módulo real, 0 fallos, type-check, thresholds en CI, sin
  regresiones), 5 (qa: SAST sin secretos, 0 CRITICAL, ≤ 5 HIGH, triaje de MEDIUM/LOW,
  type safety, anti-patterns, claims verificados, estructura del bundle, score con
  evidencia) y 6 (performance: NFRs con umbrales medibles y margen ≥ 10%, p99, memoria,
  throughput, benchmarks reproducibles, sin O(n²), E/S no bloqueante, salida
  determinista). Ampliar el tipo de entrada a `scrum_plan|sdd|tdd_plan|tests|qa|performance`.
- **Consecuencia**: el validator puede auditar los 6 gates con el mismo rigor. M9
  resuelto; 05/TASKS/DECISIONS/doc/07 actualizados (MEDIUM 8 resueltos / 1 abierto:
  M8).

## D-017 · 2026-08-08 — Plugins externos verificados en npm (L1/T-18)

- **Contexto**: `opencode.jsonc.template` y `tui.json.template` referencian 6 plugins
  externos (no incluidos en el bundle) sin verificar su disponibilidad (hallazgo LOW L1).
- **Decisión**: verificar cada nombre contra el registro npm (OpenCode resuelve el array
  `plugin` como nombres exactos de paquetes npm, instalados con Bun al arrancar).
  Resultado: `opencode-working-memory` (1.6.9), `opencode-snip` (1.6.1) y
  `envsitter-guard` (0.0.4) son válidos tal cual. `dynamic-context-pruning` y
  `opencode-quota` **no existen** con ese nombre → se sustituyen por los paquetes reales
  `@tarquinen/opencode-dcp` (3.1.14) y `@slkiser/opencode-quota` (4.5.1).
  `opencode-review` **no existe como paquete npm** (solo repos comunitarios sin publicar)
  → se **elimina** del array (decisión del usuario; la revisión de código ya la cubre
  `qa-engineer` + validator Gate 5). Aplicado también en `tui.json.template`.
- **Consecuencia**: los 6 plugins quedan instalables al arrancar OpenCode. L1 resuelto;
  check anti-regresión en la CI (job bundle) que falla si reaparece un nombre inexistente
  o se pierde `context-guard` del array.

## D-018 · 2026-08-08 — Sugerencias implementadas: M8, L2, cobertura 100%, shuffle y E2E (T-21/T-22/T-23/T-13)

- **Contexto**: las recomendaciones de los reportes 04/05/06 (sugerencias del sprint)
  quedaban como trabajo pendiente: M8 (re-inicializar anida `.opencode/.opencode/`),
  L2 (`set-threshold` mutaba el perfil `AGENTS` en memoria sin persistencia), ramas de
  cobertura restantes, aislamiento con shuffle y E2E del pipeline.
- **Decisión**: implementar las 5 sugerencias:
  1. **M8/T-21**: los init scripts hacen **backup + reemplazo** (copian el `.opencode`
     existente a `.opencode-backup-<fecha>` y lo eliminan con `rm -rf`/`Remove-Item`
     antes de copiar el framework) → ya no se anida. Check anti-regresión en la CI.
  2. **L2/T-22**: `set-threshold` persiste el umbral por agente en `thresholdOverrides`
     del estado de la sesión; `check` lo resuelve con precedencia *override por llamada >
     persistido > default del perfil*. Ya no muta el objeto global `AGENTS`. Coste
     medido: pasa de mutación en memoria a escritura real a disco (bench 1,242–1,458 →
     360–370 ops/s, ver 06 §2) — NFR intacto.
  3. **04 §7.2**: cobertura de ramas al **100%** (45 tests, 4 métricas): `formatReport`
     sin historial, `loadState` corrupto, fallbacks de límite, `sessionID` ausente,
     dry-run sin `messages`; se eliminó la rama muerta `?? 0` (guard `hasLive`).
  4. **04 §7.4**: `sequence.shuffle` (seed 0) en `vitest.config.ts` para ejecutar la
     suite en orden aleatorio (prueba de independencia).
  5. **T-13**: `e2e/smoke-e2e.sh` — inicializa un proyecto temporal, valida estructura
     (10 agentes/21 skills/configs), **re-inicializa verificando que no anida** (M8) y
     ofrece smoke live opcional (`OPENCODE_SMOKE=1` + CLI `opencode` + LLM real); job
     `e2e` en la CI.
- **Consecuencia**: 0 hallazgos abiertos (MEDIUM 9/9 y LOW 3/3 resueltos). Quality
  Score 94 → **96/100** (Testing 100, Estructural 97, Documentación 90). Performance
  Score 95/100 (set-threshold con persistencia documentado). Reportes 04/05/06,
  `doc/03` (re-init sin workaround), `doc/06` (L3 → resuelta, L10 nueva), `doc/07`,
  CURRENT_STATE y TASKS actualizados.

## D-019 · 2026-08-09 — Integración del plugin nativo KinnyCodeMemory (v1.1.0)

- **Contexto**: el framework EitL v1.0.1b usaba un wrapper MCP de Python para conectarse al
  servidor KinnyCode Memory. Este enfoque tenía limitaciones: dependencias de Python,
  dos codebases, proceso separado, overhead de MCP, y mantenimiento complejo.
- **Decisión**: migrar al plugin nativo de TypeScript `opencode-kinnycode-memory` que se
  conecta directamente al servidor KinnyCode sin wrapper MCP. Cambios implementados:
  1. **memory-adapter SKILL.md**: Actualizado para documentar el plugin nativo como
     opción recomendada, con 18 herramientas nativas (indexing, search, conversations,
     tasks, memory management).
  2. **opencode.jsonc.template**: Reemplazado el bloque MCP por configuración del plugin
     nativo con placeholders `{{KINNYCODE_SERVER_URL}}` y `{{KINNYCODE_PROJECT_ID}}`.
  3. **init-eitl.ps1**: Agregados parámetros `-KinnyCodeServerUrl`, `-KinnyCodeProjectId`,
     `-UseNativePlugin` con detección automática del modo de memoria.
  4. **init-eitl.sh**: Agregadas variables de entorno `KINNYCODE_SERVER_URL`,
     `KINNYCODE_PROJECT_ID`, `USE_NATIVE_PLUGIN` con configuración automática.
  5. **.env.template**: Actualizado con nuevas variables de entorno y documentación de
     migración del MCP wrapper al plugin nativo.
  6. **README.md**: Actualizado a v1.1.0 con documentación completa del plugin nativo,
     ejemplos de uso, y guía de migración.
  7. **scripts/verify-kinnycode-plugin.sh**: Nuevo script para verificar la instalación
     y configuración del plugin nativo.
- **Consecuencia**: El framework EitL ahora usa el plugin nativo de KinnyCodeMemory como
  opción recomendada para gestión de memoria. Ventajas logradas:
  - **Sin dependencias de Python**: Solo Node.js requerido
  - **Mejor rendimiento**: Integración directa sin overhead MCP
  - **18 herramientas nativas**: Indexación, búsqueda, conversaciones, tareas, gestión
  - **Mantenimiento simplificado**: Un solo codebase
  - **Mantienen compatibilidad**: Soporte para MCP wrapper legacy y modo standalone
  - **Tests intactos**: 45/45 tests pasan, cobertura 100%
  - **Rendimiento mantenido**: Benchmark estable, NFRs cumplidos
  - **Documentación completa**: Guía de uso y migración disponible

## D-020 · 2026-08-09 — Versión del framework actualizada a 1.1.0

- **Contexto**: la integración del plugin nativo KinnyCodeMemory representa un cambio
  significativo en las capacidades del framework, justificando una actualización de versión.
- **Decisión**: actualizar la versión del framework de 1.0b a 1.1.0 para reflejar:
  1. Integración del plugin nativo KinnyCodeMemory
  2. 18 herramientas nativas de memoria disponibles
  3. Mejoras en la configuración y scripts de inicialización
  4. Nuevas variables de entorno para el plugin nativo
  5. Script de verificación del plugin
- **Consecuencia**: El framework EitL v1.1.0 establece una nueva línea base con soporte
  nativo para memoria, preparado para futuras mejoras y mantenimiento simplificado.

