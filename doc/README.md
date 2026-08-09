# 📘 Manual de Uso — EitL Framework v1.0b

> **Framework**: Engineering in the Loop (EitL) para OpenCode-AI
> **Versión**: 1.0b (2026-08-08)
> **Pipeline**: 10 agentes · 21 skills · 6 gates · Full QA

Este manual es la guía de referencia completa para instalar el framework, inicializar
**proyectos nuevos** y **proyectos existentes**, y trabajar **con o sin sistemas de memoria**.

---

## 📑 Índice del manual

| Capítulo | Contenido | Audiencia |
|----------|-----------|-----------|
| [01 · Instalación](01-instalacion.md) | Requisitos previos, instalación en Windows/Linux/macOS, verificación de la estructura, política de ejecución y verificación opcional del framework (tests). | Todos |
| [02 · Inicializar un proyecto nuevo](02-inicializar-proyecto-nuevo.md) | Crear un proyecto desde cero: preparación, variables de entorno, ejecución de los scripts de inicialización, modo **sin memoria** (standalone) y modo **con memoria** (KinnyCode, Mem0, LanceDB), verificación post-inicialización y primer arranque del pipeline. | Todos |
| [03 · Inicializar un proyecto existente](03-inicializar-proyecto-existente.md) | Adjuntar EitL a un proyecto que ya tiene código: backup automático, precauciones, inicialización con y sin memoria, y migración de memoria/estado entre proyectos (export/import). | Equipos con proyectos en curso |
| [04 · Memoria](04-memoria.md) | Sistemas de memoria soportados, detección automática, configuración detallada por backend, capas de memoria (C1–C4), exportación/importación y cómo pasar de standalone a memoria. | Todos |
| [05 · Pipeline y comandos](05-pipeline-y-comandos.md) | Referencia completa de comandos (`/start-SDD`, `/run-tests`, `/qa-check`, `/perf-test`, `/yolo`, etc.), secuencia del pipeline, los 6 gates de validación y el plugin `context-guard`. | Todos |
| [06 · Solución de problemas](06-solucion-de-problemas.md) | Problemas frecuentes y su solución, limitaciones conocidas y checklist de verificación post-inicialización. | Todos |
| [07 · QA y auditoría](07-qa.md) | Resumen de la línea base QA de 1.0b (tests, calidad, rendimiento) y comandos para re-ejecutar la auditoría. | Desarrolladores |

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
| Ya inicialicé y quiero usar el pipeline | [05 · Pipeline y comandos](05-pipeline-y-comandos.md) |
| Algo falla o no arranca | [06 · Solución de problemas](06-solucion-de-problemas.md) |
| Quiero re-ejecutar la auditoría QA o ver su resumen | [07 · QA y auditoría](07-qa.md) |
