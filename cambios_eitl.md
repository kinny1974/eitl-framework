### Resumen de Cambios Realizados
  #### 1. Estructura de Carpetas por Plan (scrum-master.md)

  Ahora cada plan de desarrollo se almacena en su propio directorio con un
  identificador descriptivo (slug):
    eitl-artifacts/
    ├── <plan-name>/                           # Carpeta dedicada para
  cada plan
    │   ├── 01_Plan_Scrum.md
    │   ├── 02_Architecture_SDD.md
    │   ├── 03_Plan_TDD.md
    │   ├── 04_Test_Report.md
    │   ├── 05_QA_Report.md
    │   ├── 06_Performance_Report.md
    │   └── CURRENT_STATE.md                  # Estado específico del plan
    └── CURRENT_STATE.md                      # Índice global y puntero al
  plan activo
  #### 2. Convención y Nomenclatura del Plan
  • Explícito: Si el usuario especifica el nombre del plan en el comando:
  /start-SDD auth-jwt "Implementar autenticación con JWT" → Carpeta: eitl-
  artifacts/auth-jwt/
  • Automático / Inferido: Si solo se pasa el requerimiento:
  /start-SDD "Optimización de consultas de inventario" → El Scrum Master
  genera automáticamente el slug (ej. optimizacion-consultas-inventario).

  #### 3. Comandos Ajustados con Soporte de Plan

  • /start-SDD [plan-name] [requirement] o /start-SDD [requirement]
  • /start-TDD [plan-name]
  • /start-IMPL [plan-name] [task-id]
  • /run-tests [plan-name] [component]
  • /qa-check [plan-name]
  • /perf-test [plan-name]
  • /regen [plan-name] [scrum|sdd|tdd]
  • /status [plan-name]
  • /blocker [plan-name] [msg]

  #### 4. Orquestación y Delegación Explícita

  El Scrum Master pasa explícitamente la ruta ../eitl-artifacts/<plan-
  name>/<archivo>.md a cada subagente durante la delegación:

  1. @product-owner → genera ../eitl-artifacts/<plan-name>/01_Plan_Scrum.
  md
  2. @validator (Gate 1) → valida ../eitl-artifacts/<plan-
  name>/01_Plan_Scrum.md
  3. @architect → lee 01_Plan_Scrum.md y genera ../eitl-artifacts/<plan-
  name>/02_Architecture_SDD.md
  4. @validator (Gate 2) → valida ../eitl-artifacts/<plan-
  name>/02_Architecture_SDD.md
  5. @tdd-engineer → lee 02_Architecture_SDD.md y genera ../eitl-
  artifacts/<plan-name>/03_Plan_TDD.md
  6. @validator (Gate 3) → valida ../eitl-artifacts/<plan-
  name>/03_Plan_TDD.md
  7. @test-runner → genera ../eitl-artifacts/<plan-name>/04_Test_Report.md
  8. @qa-engineer → genera ../eitl-artifacts/<plan-name>/05_QA_Report.md
  9. @performance-engineer → genera ../eitl-artifacts/<plan-
  name>/06_Performance_Report.md
  ──────
  ### Archivos Modificados

  • scrum-master.md: Rutas, reglas de slug, comandos y orquestación por
  carpeta de plan.
  • product-owner.md: Entrada y salida dirigidas a ../eitl-
  artifacts/<plan-name>/01_Plan_Scrum.md.
  • architect.md: Entrada y salida dirigidas a ../eitl-artifacts/<plan-
  name>/02_Architecture_SDD.md.
  • tdd-engineer.md: Entrada y salida dirigidas a ../eitl-artifacts/<plan-
  name>/03_Plan_TDD.md.
  • test-runner.md: Reporte dirigido a ../eitl-artifacts/<plan-
  name>/04_Test_Report.md.
  • qa-engineer.md: Reporte dirigido a ../eitl-artifacts/<plan-
  name>/05_QA_Report.md.
  • performance-engineer.md: Reporte dirigido a ../eitl-artifacts/<plan-
  name>/06_Performance_Report.md.
  • validator.md: Validación de artefactos por ruta de plan.
  • SKILL.md: Persistencia de estado por carpeta de plan.
  • templates: 01_Plan_Scrum.md.template, 02_Architecture_SDD.md.template
  y 03_Plan_TDD.md.template actualizadas con <plan-name>.