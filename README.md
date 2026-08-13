# EitL Framework v1.0b

**Framework para configurar y ejecutar pipelines completos (E) de datos usando OpenCode.**

## 🚀 Características Principales

- **Gestión automática de contexto** – Monitorea el uso de la ventana de contexto (128k tokens) y actúa automáticamente para evitar colapsos.
- **Context Guard** – Skill que detecta el uso de tokens y ejecuta guardado + compactación.
- **Memory Adapter** – Compatible con KinnyCodeMemory o modo standalone.
- **Automatización** – Acciones automáticas en WARNING (83k-109k) y CRITICAL (≥110k).

## 📌 Gestión de Memoria

### Políticas de Umbral

| Nivel | Umbral | Acción |
|-------|---------|---------|
| **OK** | < 65% (0‑83k) | Continuar normalmente |
| **⚠️ WARNING** | 65‑85% (83k‑109k) | **Auto-save a memoria + compactación** |
| **🚨 CRITICAL** | ≥ 86% (≥ 110k) | **Auto-save a memoria + compactación** |

### Flujo de Acción Automática (WARNING)

Cuando el contexto alcanza **83k tokens o más** (pero antes de 110k):

1. **Guardar conversación** – `guardar_conversacion()`
2. **Guardar decisiones** – `guardar_decision()` (si aplican)
3. **Guardar tareas** – `guardar_tarea()` (si hay tareas en progreso)
4. **Compactar** – Preserva los últimos 10 mensajes, resuma el resto y elimina bloqueos resueltos.

### Flujo de Acción Automática (CRITICAL)

Cuando el contexto alcanza **≥ 110k tokens**:

1. **Guardar conversación** – `guardar_conversacion()`
2. **Guardar decisiones** – `guardar_decision()`
3. **Guardar tareas** – `guardar_tarea()`
4. **Compactar** – Preserva los últimos 10 mensajes, resuma el resto y limpia bloqueos.

## 🧩 Componentes Principales

| Componente | Función |
|------------|----------|
| **context-guard** | Monitoriza el uso de contexto y ejecuta guardado/compactación |
| **memory-adapter** | Gestiona la integración con KinnyCodeMemory o modo standalone |
| **scrum-master** | Regla obligatoria: verificar contexto antes de delegar tareas pesadas |
| **memory-adapter** | Compatibilidad con KinnyCodeMemory (servidor local) o modo standalone (archivos en `eitl-artifacts/`) |

## 🚀 Uso Básico

```bash
# Iniciar el pipeline
opencode

# Verificar estado del contexto
context-guard({ action: "check", agent: "auto" })

# Forzar compactación manual (si necesitas)
context-guard({ action: "compact", agent: "auto" })
```

## 📁 Estructura del Repositorio

```
EITL_FRAMEWORK/
├── framework/
│   ├── .opencode/plugins/context-guard/
│   ├── .opencode/skills/context-guard/SKILL.md
│   └── .opencode/agents/scrum-master.md
├── eteil-framework/
│   ├── README.md
│   └── doc/
│       └── memoria-policy-completada.md
├── init-scripts/
│   ├── init-eitl.ps1
│   └── init-eitl.sh
└── project-config-template/opencode.jsonc.template
```

## 📝 Documentación

- **[Memoria Policy Completada](doc/memoria-policy-completada.md)** – Política detallada de gestión de contexto.
- **[README.md](README.md)** – Guía de uso y flujo de trabajo.

## 🔒 Seguridad

- **Never lose**: Decisiones, estado de tareas y cambios de archivos nunca se pierden.
- **Logs**: Todas las compactaciones se registran en `context-guard.log`.
- **Autenticación**: Cada comando requiere autorización del usuario.

---

*Versión: EitL Framework v1.0b*
*Estado: Ready for production use*
