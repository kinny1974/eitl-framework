# 📘 Manual de Uso — EitL Framework v1.1.0

> **Framework**: Engineering in the Loop (EitL) para OpenCode-AI
> **Versión**: 1.1.0 (2026-08-09)
> **Pipeline**: 10 agentes · 21 skills · 6 gates · Full QA
> **Memoria**: Plugin nativo KinnyCodeMemory (18 herramientas)

Este manual es la guía de referencia completa para instalar el framework, inicializar
**proyectos nuevos** y **proyectos existentes**, y trabajar **con o sin sistemas de memoria**.

---

## 📑 Índice del manual

| Capítulo | Contenido | Audiencia |
|----------|-----------|-----------|
| [01 · Instalación](01-instalacion.md) | Requisitos previos, instalación en Windows/Linux/macOS, verificación de la estructura, política de ejecución, instalación del plugin KinnyCodeMemory y verificación opcional del framework (tests). | Todos |
| [02 · Inicializar un proyecto nuevo](02-inicializar-proyecto-nuevo.md) | Crear un proyecto desde cero: preparación, variables de entorno, ejecución de los scripts de inicialización, modo **sin memoria** (standalone) y modo **con memoria** (plugin nativo KinnyCodeMemory, MCP wrapper legacy, Mem0, LanceDB) — incluido **servidor de memoria remoto** (otro equipo de la red), verificación post-inicialización y primer arranque del pipeline. | Todos |
| [03 · Inicializar un proyecto existente](03-inicializar-proyecto-existente.md) | Adjuntar EitL a un proyecto que ya tiene código: backup automático, precauciones, inicialización con y sin memoria, y migración de memoria/estado entre proyectos (export/import). | Equipos con proyectos en curso |
| [04 · Memoria](04-memoria.md) | Sistemas de memoria soportados (plugin nativo KinnyCodeMemory recomendado), detección automática, configuración detallada por backend, 18 herramientas nativas, capas de memoria (C1–C4), exportación/importación y cómo pasar de standalone a memoria. | Todos |
| [05 · Pipeline y comandos](05-pipeline-y-comandos.md) | Referencia completa de comandos (`/start-SDD`, `/run-tests`, `/qa-check`, `/perf-test`, `/yolo`, etc.), secuencia del pipeline, los 6 gates de validación y el plugin `context-guard`. | Todos |
| [06 · Solución de problemas](06-solucion-de-problemas.md) | Problemas frecuentes y su solución (incluido plugin KinnyCodeMemory), limitaciones conocidas y checklist de verificación post-inicialización. | Todos |
| [07 · QA y auditoría](07-qa.md) | Resumen de la línea base QA de 1.1.0 (tests, calidad, rendimiento) y comandos para re-ejecutar la auditoría. | Desarrolladores |

---

## 🗺️ Estructura del framework (referencia rápida)

```
eitl-framework/
├── framework/                     ← REUTILIZABLE (no editar directamente)
│   └── .opencode/
│       ├── agents/               ← 10 agentes del pipeline
│       ├── skills/               ← 21 skills (memoria, QA, portabilidad, …)
│       ├── plugin/               ← context-guard.ts + entorno de pruebas (vitest)
│       ├── command/              ← comandos TUI (/context-guard)
│       └── eitl/                 ← plantillas de artefactos + estado inicial
├── project-config-template/      ← plantillas de configuración generadas
├── init-scripts/
│   ├── init-eitl.ps1             ← inicializador Windows (PowerShell)
│   └── init-eitl.sh              ← inicializador Linux/macOS (Bash)
├── scripts/
│   └── verify-kinnycode-plugin.sh ← verificación del plugin KinnyCodeMemory
├── doc/                          ← este manual
├── QUICKSTART.md                 ← arranque rápido (5 minutos)
└── README.md                     ← documentación principal
```

**Regla de oro**: todo lo específico del proyecto (artefactos, estado, decisiones) va en
`../eitl-artifacts/` (hermano del proyecto). `.opencode/` es el framework: si necesitas
cambiar algo, modifica el framework y vuelve a inicializar.

---

## 🔀 ¿Por dónde empiezo?

| Situación | Capítulo |
|-----------|----------|
| Nunca instalé el framework | [01 · Instalación](01-instalacion.md) |
| Quiero crear un proyecto desde cero | [02 · Inicializar un proyecto nuevo](02-inicializar-proyecto-nuevo.md) |
| Quiero aplicar EitL a un repo que ya existe | [03 · Inicializar un proyecto existente](03-inicializar-proyecto-existente.md) |
| Quiero entender memoria standalone vs servidor | [04 · Memoria](04-memoria.md) |
| Quiero usar el plugin nativo KinnyCodeMemory | [04 · Memoria](04-memoria.md) sección 4.3 |
| Ya inicialicé y quiero usar el pipeline | [05 · Pipeline y comandos](05-pipeline-y-comandos.md) |
| Algo falla o no arranca | [06 · Solución de problemas](06-solucion-de-problemas.md) |
| Quiero re-ejecutar la auditoría QA o ver su resumen | [07 · QA y auditoría](07-qa.md) |

---

## 🚀 Inicio rápido con plugin KinnyCodeMemory

```bash
# 1. Instalar el plugin
cd F:\kinnyCodeMemory
git clone https://github.com/KinnyCode/plugin-kinnycode.git
cd plugin-kinnycode
npm install
npm run build

# 2. Configurar variables de entorno
export KINNYCODE_SERVER_URL=http://192.168.2.111:8007
export KINNYCODE_PROJECT_ID=6b6a8b869aea48ad
export MEMORY_ENABLED=true
export USE_NATIVE_PLUGIN=true
export CPU_BASEURL=http://localhost:11434/v1
export API_KEY=not-needed

# 3. Crear e inicializar proyecto
mkdir -p ~/projects/mi-proyecto
cd ~/projects/mi-proyecto
bash ~/tools/eitl-framework/init-scripts/init-eitl.sh "mi-proyecto"

# 4. Verificar instalación
bash ~/tools/eitl-framework/scripts/verify-kinnycode-plugin.sh

# 5. Iniciar OpenCode
opencode
```

---

## 📊 Cambios en v1.1.0

### ✅ Nuevas características

- **Plugin Nativo KinnyCodeMemory**: 18 herramientas nativas para gestión de memoria
- **Sin dependencias Python**: Solo Node.js requerido
- **Mejor rendimiento**: Integración directa en OpenCode
- **Script de verificación**: `scripts/verify-kinnycode-plugin.sh`
- **Variables de entorno nuevas**: `KINNYCODE_SERVER_URL`, `KINNYCODE_PROJECT_ID`, `USE_NATIVE_PLUGIN`

### 🔧 Archivos actualizados

- `memory-adapter/SKILL.md`: Documentación del plugin nativo
- `opencode.jsonc.template`: Configuración del plugin nativo
- `init-eitl.ps1`: Parámetros para plugin nativo
- `init-eitl.sh`: Variables de entorno para plugin nativo
- `.env.template`: Nuevas variables de entorno
- `README.md`: Documentación completa de v1.1.0
- `QUICKSTART.md`: Guía de inicio rápido actualizada
- `doc/01-instalacion.md`: Instrucciones de instalación actualizadas
- `doc/04-memoria.md`: Guía completa de memoria con plugin nativo
- `doc/06-solucion-de-problemas.md`: Solución de problemas del plugin

### 📈 Métricas

- **Tests**: 45/45 ✅
- **Cobertura**: 100% (stmts/ramas/funcs/líneas) ✅
- **Type-check**: 0 errores ✅
- **Benchmark**: Estable, NFRs cumplidos ✅

---

**← [QUICKSTART](../QUICKSTART.md)** · **Siguiente → [01 · Instalación](01-instalacion.md)**
