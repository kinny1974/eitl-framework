# 05 · Pipeline y comandos

> **Objetivo**: referencia completa de comandos, agentes, fases y gates del pipeline EitL,
> más el uso del plugin `context-guard`.

---

## 5.1 Los 10 agentes del pipeline

| Agente | Fase | Salida |
|--------|------|--------|
| **scrum-master** | Orquestación | Estado actual del proyecto (único agente que habla con el usuario) |
| **product-owner** | Diseño | `01_Plan_Scrum.md` |
| **architect** | Diseño | `02_Architecture_SDD.md` |
| **tdd-engineer** | Diseño | `03_Plan_TDD.md` |
| **validator** | Todos los gates | Reportes de validación (APPROVED/REJECTED/NEEDS_REVISION) |
| **test-runner** | QA | `04_Test_Report.md` |
| **qa-engineer** | QA | `05_QA_Report.md` |
| **performance-engineer** | QA | `06_Performance_Report.md` |
| **backend-expert** | Implementación | Código backend |
| **spec-lead** | Arquitectura | Especificaciones técnicas |

> ℹ️ Nomenclatura unificada (M3/T-15): todos los artefactos del pipeline usan nombres en
> inglés — `01_Plan_Scrum.md` → `02_Architecture_SDD.md` → `03_Plan_TDD.md` — y la
> plantilla del bundle se llama `02_Architecture_SDD.md.template`.

---

## 5.2 Referencia de comandos

| Comando | Fase | Agente | Salida |
|---------|------|--------|--------|
| `/start-SDD [plan-name] [req]` | Diseño | product-owner → architect → tdd-engineer | `01_Plan_Scrum.md` → `02_Architecture_SDD.md` → `03_Plan_TDD.md` |
| `/start-TDD [plan-name]` | Diseño (salto) | architect → tdd-engineer | SDD → `03_Plan_TDD.md` |
| `/start-IMPL [plan-name] [id]` | Implementación | (delegación a dev) | Código fuente |
| `/run-tests [plan-name] [comp]` | QA | test-runner | `04_Test_Report.md` |
| `/qa-check [plan-name]` | QA | qa-engineer | `05_QA_Report.md` |
| `/perf-test [plan-name]` | QA | performance-engineer | `06_Performance_Report.md` |
| `/regen [plan-name] [scrum\|sdd\|tdd]` | Control | — | Regenera el artefacto indicado |
| `/status [plan-name]` | Control | scrum-master | Estado actual del plan / pipeline |
| `/blocker [plan-name] [msg]` | Control | scrum-master | Registra un bloqueador para el plan |
| `/context-guard check [agente]` | Control | — | Chequea la ventana de contexto |
| `/yolo on [plan-name]` / `/yolo off` | Control | scrum-master | Activa/desactiva el modo autónomo |

---

## 5.3 Secuencia del pipeline (flujo obligatorio)

```
1.  /start-SDD [requerimiento]
    → @product-owner genera 01_Plan_Scrum.md
    → @validator valida GATE 1 (scrum_plan)
    → Si REJECTED: máx. 3 reintentos, luego escalar a humano

2.  (automático) @architect genera 02_Architecture_SDD.md
    → @validator valida GATE 2 (sdd)
    → Si REJECTED: máx. 3 reintentos

3.  (automático) @tdd-engineer genera 03_Plan_TDD.md
    → @validator valida GATE 3 (tdd_plan)
    → Si REJECTED: máx. 3 reintentos

4.  /start-IMPL [id]
    → Implementación de código (agente dev o humano)

5.  /run-tests
    → @test-runner ejecuta la suite y genera 04_Test_Report.md
    → @validator valida GATE 4 (tests) — cobertura ≥ 80%, 0 fallos

6.  /qa-check
    → @qa-engineer analiza calidad y genera 05_QA_Report.md
    → @validator valida GATE 5 (qa) — 0 issues CRITICAL

7.  /perf-test
    → @performance-engineer valida NFRs y genera 06_Performance_Report.md
    → @validator valida GATE 6 (performance) — todos los NFRs cumplidos

8.  Pipeline COMPLETADO
```

**Reglas del orquestador**:
- Ninguna fase comienza sin la aprobación de la anterior.
- La validación de gates es obligatoria en cada transición.
- Ante un gate fallido: hasta 3 reintentos y luego escalar al humano.
- El estado se mantiene en memoria (o en archivos en modo standalone).

---

## 5.4 Los 6 gates de validación

| Gate | Artefacto | Criterios de aprobación (resumen) |
|------|-----------|------------------------------------|
| **Gate 1** | `01_Plan_Scrum.md` | Historias verificables, DoD definido, trazabilidad (checklist de 10 ítems) |
| **Gate 2** | `02_Architecture_SDD.md` | ADRs, modelos de datos, contratos de API, NFRs (10 ítems) |
| **Gate 3** | `03_Plan_TDD.md` | Pirámide 80/15/5, edge cases, fixtures (10 ítems) |
| **Gate 4** | `04_Test_Report.md` | Cobertura ≥ 80% y 0 tests fallidos |
| **Gate 5** | `05_QA_Report.md` | 0 issues CRITICAL y ≤ 5 HIGH |
| **Gate 6** | `06_Performance_Report.md` | Todos los NFRs cumplidos con margen ≥ 10% |

> ⚠️ Categorías de rechazo del validator: **INCOMPLETE** (faltan secciones),
> **INCONSISTENT** (contradice el artefacto previo), **UNVERIFIABLE** (no testeable),
> **LOW_QUALITY** (calidad insuficiente).

---

## 5.5 Protección de contexto (`context-guard`)

Antes de **cada delegación** a un subagente, el scrum-master invoca:

```
/context-guard check [agente]        # o bien: /cg
```

| Resultado | Acción |
|-----------|--------|
| ✅ OK (bajo umbral seguro) | Continuar |
| ⚠️ WARNING (sobre umbral seguro) | Considerar compactación antes de delegar |
| 🚨 CRITICAL (sobre umbral crítico) | Compactar (`/context-guard compact`) o abortar |

Otras acciones:

```
/context-guard compact [agente] [--dry-run]
/context-guard switch-agent <agente>
/context-guard report
```

Perfiles por agente (umbrales seguro/crítico): scrum-master 65/80 · product-owner 60/75 ·
architect 55/70 · tdd-engineer 60/78 · validator 65/80.

> ℹ️ Con la API actual de ToolContext (que no expone `tokenUsage`), si el runtime no
> inyecta métricas de sesión, el guard reporta **"no disponibles"** con estado preventivo
> OK y usa, si existen, las métricas del último check persistido (marcadas como
> "persistido").

> El plugin persiste alertas, compactaciones y cambios de agente por sesión en
> `.opencode/.context-guard/<sessionId>.json` (o el directorio definido por
> `OPENCODE_STATE_DIR`).

---

## 5.6 Modo YOLO (autónomo)

`/yolo on` activa el pipeline sin pausas de aprobación entre fases:

- Auto-aprueba delegaciones y comandos.
- Máx. 3 reintentos por gate.
- El contexto se verifica automáticamente entre fases.
- El estado YOLO se persiste en memoria.
- Permanece activo hasta `/yolo off` (o "stop autonomous mode").

> ⚠️ Recomendado solo para flujos maduros: elimina la supervisión humana de los gates.

---

## 5.7 Ubicación de los artefactos (Estructura por Plan)

Los artefactos de cada funcionalidad o plan se organizan en su propio subdirectorio dentro de `../eitl-artifacts/`:

```
../eitl-artifacts/               ← SIEMPRE fuera de .opencode/
├── <plan-name>/                 # Carpeta dedicada para cada plan (ej: auth-jwt)
│   ├── 01_Plan_Scrum.md
│   ├── 02_Architecture_SDD.md
│   ├── 03_Plan_TDD.md
│   ├── 04_Test_Report.md
│   ├── 05_QA_Report.md
│   ├── 06_Performance_Report.md
│   └── CURRENT_STATE.md        # Estado específico del plan
├── CURRENT_STATE.md            # Índice global y puntero al plan activo
├── TASKS.md                    (standalone global)
└── DECISIONS.md                (standalone global)
```

**Regla de oro**: los artefactos **nunca** se escriben dentro de `.opencode/` ni directamente en la raíz de `../eitl-artifacts/` (cada plan tiene su subcarpeta dedicada).

---

**← [04 · Memoria](04-memoria.md)** · **Siguiente → [06 · Solución de problemas](06-solucion-de-problemas.md)**

