# 00 - Glosario

> **Objetivo**: definiciones de los terminos usados en EitL y OpenCode.

---

## Terminos de EitL

| Termino | Definicion |
|---------|------------|
| **EitL** | Engineering in the Loop. Framework de ingenieria de software con agentes. |
| **Pipeline** | Secuencia de fases que van desde el requerimiento hasta la implementacion. |
| **Gate** | Punto de validacion obligatorio entre fases del pipeline. |
| **Artefacto** | Documento generado por el pipeline (SDD, TDD, reportes). |
| **Agente** | Componente especializado que ejecuta una tarea especifica. |
| **Sprint** | Iteracion del pipeline con un objetivo definido. |
| **Standalone** | Modo de operacion sin servidor de memoria externo. |

---

## Terminos de los Agentes

| Agente | Que hace |
|--------|----------|
| **scrum-master** | Orquesta el pipeline. Unico agente que habla con el usuario. |
| **product-owner** | Genera el plan Scrum (01_Plan_Scrum.md). |
| **architect** | Disena la arquitectura (02_Architecture_SDD.md). |
| **tdd-engineer** | Crea el plan de pruebas (03_Plan_TDD.md). |
| **validator** | Valida que cada artefacto cumpla los criterios. |
| **test-runner** | Ejecuta las pruebas y genera reportes. |
| **qa-engineer** | Analiza la calidad del codigo. |
| **performance-engineer** | Valida requisitos de rendimiento. |
| **backend-expert** | Implementa codigo backend. |
| **spec-lead** | Genera especificaciones tecnicas. |

---

## Terminos de Gates

| Gate | Que valida |
|------|------------|
| **Gate 1 (scrum_plan)** | El plan Scrum tiene historias verificables y DoD definido. |
| **Gate 2 (sdd)** | La arquitectura tiene ADRs, modelos de datos y contratos de API. |
| **Gate 3 (tdd_plan)** | El plan de pruebas sigue la piramide 80/15/5. |
| **Gate 4 (tests)** | Cobertura >= 80% y 0 tests fallidos. |
| **Gate 5 (qa)** | 0 issues CRITICAL y <= 5 HIGH. |
| **Gate 6 (performance)** | Todos los NFRs cumplidos con margen >= 10%. |

---

## Terminos de Memoria

| Termino | Definicion |
|---------|------------|
| **Memoria semantica** | Busqueda de contexto basada en significado, no solo palabras clave. |
| **Project ID** | Identificador unico para un proyecto en la memoria. |
| **Indexar** | Analizar y almacenar codigo/documentos en la memoria. |
| **Consolidar** | Unir y limpiar memorias duplicadas o redundantes. |
| **Embedding** | Representacion numerica de texto para busqueda semantica. |

---

## Terminos de OpenCode

| Termino | Definicion |
|---------|------------|
| **TUI** | Terminal User Interface. Interfaz de usuario en terminal. |
| **Plugin** | Componente que agrega funcionalidad a OpenCode. |
| **Skill** | Instruccion especializada que un agente puede ejecutar. |
| **Context-guard** | Plugin que monitorea el uso de contexto en la sesion. |
| **YOLO** | Modo autonomo sin pausas de aprobacion. |

---

## Terminos Tecnicos

| Termino | Definicion |
|---------|------------|
| **SDD** | Software Design Document. Documento de diseno de software. |
| **TDD** | Test-Driven Development. Desarrollo orientado a pruebas. |
| **NFR** | Non-Functional Requirement. Requisito no funcional. |
| **ADR** | Architecture Decision Record. Registro de decisiones de arquitectura. |
| **DoD** | Definition of Done. Criterios de finalizacion de una tarea. |
| **LanceDB** | Base de datos vectorial para busqueda semantica. |
| **Ollama** | Herramienta para ejecutar modelos de IA localmente. |

---

## Siglas Comunes

| Sigla | Significado |
|-------|-------------|
| **API** | Application Programming Interface |
| **CI/CD** | Continuous Integration / Continuous Deployment |
| **QA** | Quality Assurance |
| **CRITICAL** | Problema grave que bloquea el uso |
| **HIGH** | Problema importante que debe resolverse pronto |
| **MEDIUM** | Problema que puede esperar |
| **LOW** | Problema menor o mejora opcional |

---

## Siguiente paso

Ve a [01 - Instalacion](01-instalacion.md) para empezar.
