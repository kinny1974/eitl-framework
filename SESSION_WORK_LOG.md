# EitL Framework - Resumen de Sesión de Trabajo

**Fecha**: 2026-08-11 23:02
**Versión**: v1.0b (tag existente)
**Repositorio**: https://github.com/kinny1974/eitl-framework

---

## 🎯 Objetivo de la Sesión

Implementar **gestión automática de contexto** (context-guard) con:
- Monitoreo continuo de ventana de contexto (128k tokens)
- Auto-guardado en memoria al llegar a 110k tokens (86%)
- Compactación automática
- Integración con memory-adapter (KinnyCodeMemory / standalone)
- Configuración lista desde init (Windows + Linux)

---

## ✅ Cambios Realizados

### 1. **Skill context-guard - Actualización Completa**

**Archivo**: ramework/.opencode/skills/context-guard/SKILL.md

**Cambios**:
- Umbrales ajustados para ventana de 128k:
  - OK: < 65% (< 83k)
  - WARNING: 65-85% (83k-109k)
  - **CRITICAL: ≥ 86% (≥ 110k)**
- Acciones automáticas en CRITICAL (secuencia obligatoria):
  1. guardar_conversacion - resumen + archivos + decisiones
  2. guardar_decision - decisiones pendientes
  3. guardar_tarea - tareas en progreso
  4. compactar - preservar últimos 10 mensajes
- Integración con memory-adapter (KinnyCodeMemory / standalone)
- Perfiles por agente con umbral crítico unificado en 86%

### 2. **Agente scrum-master - Regla Obligatoria**

**Archivo**: ramework/.opencode/agents/scrum-master.md

**Cambios**:
- Sección **Context Protection (MANDATORY)** expandida
- **Regla #7**: ALWAYS load context-guard skill before heavy delegations
- Tabla de comandos pesados que requieren check previo:
  - /start-SDD → @product-owner (HIGH)
  - /start-TDD → @tdd-engineer (HIGH)
  - /run-tests → @test-runner (HIGH)
  - /qa-check → @qa-engineer (MEDIUM)
  - /perf-test → @performance-engineer (MEDIUM)
  - /regen → varies (HIGH)
- Flujo obligatorio antes de delegar:
  1. Load skill: context-guard
  2. Execute: context-guard({ action: "check", agent: "auto" })
  3. OK → proceder
  4. WARNING → avisar usuario
  5. CRITICAL → auto-save + compact → proceder
- YOLO Mode: context-guard runs automáticamente entre fases

### 3. **Plugin context-guard - Verificación de Estado**

**Ubicación**: ramework/.opencode/plugin/context-guard/

**Estado actual**:
- ✅ Código fuente existe (context-guard.ts - 430 líneas)
- ✅ Tests/benchmarks incluidos
- ✅ package.json configurado
- ⚠️ **Pendiente**: 
pm run build para generar dist/
- ⚠️ **Pendiente**: Instalación global (
pm install -g)

### 4. **Template opencode.jsonc.template - Base Actualizada**

**Archivo**: project-config-template/opencode.jsonc.template

**Estructura final**:
`jsonc
{
  "plugin": [
    ["context-guard"],
    ["memory-adapter", {
      "mode": "{{MEMORY_MODE}}",
      "serverUrl": "{{MEMORY_URL}}",
      "projectId": "{{PROJECT_ID}}",
      "fallback": "{{FALLBACK_MODE}}"
    }]
    // Plugins extra comentados (opcionales)
  ],
  "agent": { "scrum-master": { "prompt": "{file:agents/scrum-master.md}" } },
  "provider": { ... }
}
`

**Placeholders para rellenar en init**:
- {{MEMORY_MODE}} → kinny | standalone | uto
- {{MEMORY_URL}} → http://localhost:8007
- {{PROJECT_ID}} → ID del proyecto
- {{FALLBACK_MODE}} → ile | 
one

### 5. **Scripts de Inicialización - Pendientes de Actualización**

**Archivos a modificar**:
- init-scripts/init-eitl.ps1 (Windows)
- init-scripts/init-eitl.sh (Linux)

**Tareas pendientes en scripts**:
1. Detectar si context-guard necesita build y ejecutarlo
2. Generar opencode.jsonc rellenando placeholders
3. Configurar memory-adapter según elección del usuario
4. Opcional: habilitar opencode-kinnycode-memory si se solicita
5. Validación cross-platform (Windows PowerShell + Linux Bash)

---

## 📋 Estado Actual del Proyecto

### ✅ Completado
| Componente | Estado |
|------------|--------|
| Skill context-guard | ✅ Actualizada con umbrales 110k/128k |
| Agente scrum-master | ✅ Regla #7 + flujo obligatorio |
| Template opencode.jsonc.template | ✅ Estructura base lista |
| memory-adapter skill | ✅ Existe y documentado |
| Git commit + push | ✅ 3887c75 en main |

### ⚠️ Pendiente
| Tarea | Descripción |
|-------|-------------|
| Build context-guard | cd framework/.opencode/plugin/context-guard && npm run build |
| Install global context-guard | 
pm install -g framework/.opencode/plugin/context-guard |
| Actualizar init-eitl.ps1 | Auto-build, template rendering, config cross-platform |
| Actualizar init-eitl.sh | Idem para Linux |
| Probar flujo completo | Verificar auto-save + compact en CRITICAL |

---

## 🔧 Próximos Pasos Inmediatos

### 1. Compilar e instalar context-guard
`ash
# Windows PowerShell
cd F:\eitl-framework\framework\.opencode\plugin\context-guard
npm run build
npm install -g .

# Linux/macOS
cd /path/to/eitl-framework/framework/.opencode/plugin/context-guard
npm run build
npm install -g .
`

### 2. Actualizar scripts de init (Windows)
En init-scripts/init-eitl.ps1:
- Agregar detección de context-guard sin compilar
- Ejecutar 
pm run build automáticamente
- Renderizar opencode.jsonc.template con nvsubst / PowerShell
- Configurar memory-adapter según input usuario

### 3. Actualizar scripts de init (Linux)
En init-scripts/init-eitl.sh:
- Mismo flujo que Windows
- Usar nvsubst o jq para template

### 4. Validación cross-platform
Crear scripts de verificación:
- scripts/context-guard-check.ps1 (Windows)
- scripts/context-guard-check.sh (Linux)

---

## 🧪 Flujo de Prueba Esperado

Una vez completado todo:

`ash
# 1. Usuario ejecuta init
./init-eitl.ps1 -ProjectName "mi-proyecto" -MemoryMode kinny

# 2. Init hace automáticamente:
#    - Build context-guard
#    - Genera opencode.jsonc con context-guard + memory-adapter
#    - Configura KinnyCodeMemory si se eligió

# 3. Usuario abre OpenCode
opencode

# 4. Ejecuta comandos pesados
/start-SDD "Nueva feature compleja"
/run-tests

# 5. Sistema automáticamente:
#    - Monitorea contexto cada delegación
#    - Al llegar a 110k tokens (86%):
#      a) guardar_conversacion()
#      b) guardar_decision() si hay
#      c) guardar_tarea() si hay
#      d) compactar() - preserva 10 mensajes
#    - Continúa sin intervención

# 6. Verificación
context-guard({ action: "report", agent: "auto" })
# Muestra: logs, alertas, compactaciones, estado actual
`

---

## 📝 Notas Técnicas Importantes

### Cross-Platform
- **Windows**: PowerShell 7+ (.ps1), rutas con \
- **Linux/macOS**: Bash (.sh), rutas con /
- Template usa placeholders universales {{VARIABLE}}
- nvsubst (Linux) / ConvertFrom-Json + replace (Windows) para renderizado

### Memoria
- **KinnyCodeMemory**: Requiere servidor corriendo (http://localhost:8007)
- **Standalone**: Escribe en itl-artifacts/DECISIONS.md, TASKS.md, CURRENT_STATE.md
- **Fallback**: memory-adapter detecta automáticamente

### Seguridad
- Hard-stop a 95% (121k) si 3 compactaciones fallan
- Logs de todas las compactaciones para post-mortem
- Nunca perder: decisiones, tareas, archivos modificados

---

## 📌 Archivos Clave del Proyecto

| Archivo | Propósito |
|---------|-----------|
| ramework/.opencode/skills/context-guard/SKILL.md | Skill principal de gestión de contexto |
| ramework/.opencode/agents/scrum-master.md | Agente principal con regla #7 obligatoria |
| project-config-template/opencode.jsonc.template | Template base para configuración OpenCode |
| ramework/.opencode/plugin/context-guard/ | Plugin TypeScript (requiere build) |
| ramework/.opencode/skills/memory-adapter/SKILL.md | Adaptador de memoria unificado |
| init-scripts/init-eitl.ps1 | Inicializador Windows (pendiente update) |
| init-scripts/init-eitl.sh | Inicializador Linux (pendiente update) |

---

## 🏷️ Git History Reciente

`
3887c75 feat: context-guard híbrido - auto-save a memoria antes de compactar
ddb0b1d (tag: v1.0b) Release v1.0b - UX overhaul, memory optional, docs rewrite
`

---

## ✅ Checklist Final para "Listo para Producción"

- [ ] context-guard compilado (dist/ existe)
- [ ] context-guard instalado globalmente
- [ ] init-eitl.ps1 actualizado (build + template + cross-platform)
- [ ] init-eitl.sh actualizado (build + template + cross-platform)
- [ ] Scripts de verificación creados (.ps1 + .sh)
- [ ] Prueba end-to-end en Windows
- [ ] Prueba end-to-end en Linux
- [ ] Documentación actualizada (README.md, doc/04-memoria.md)
- [ ] Tag v1.0.1b o v1.1.0

---

*Documento generado automáticamente al final de la sesión de trabajo.*
