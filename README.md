# EitL Framework v3.0 (TOON Layer)

**Framework para configurar y ejecutar pipelines completos (E) de datos usando OpenCode.**

## 🚀 Características Principales

- **Gestión automática de contexto** – Monitorea el uso de la ventana de contexto (128k tokens) y actúa automáticamente para evitar colapsos.
- **Context Guard** – Skill que detecta el uso de tokens y ejecuta guardado + compactación.
- **Memory Adapter** – Compatible con KinnyCodeMemory o modo standalone.
- **Automatización** – Acciones automáticas en WARNING (83k-109k) y CRITICAL (≥110k).
- **TOON v4.1 Integration** – Capa de traducción NL → TOON para optimización de tokens (~30-50% ahorro vs JSON)
- **TOON Translator Agent** – Modelo pequeño qwen2.5-3b @ 192.168.2.111:8002/v1
- **Python Utilities** – Convertidores JSON ↔ TOON en scripts/toon/

## 🧱 TOON Architecture

```
Usuario (NL) → TOON Translator (OpenCode Subagent) → orchestrator.py (Python Gateway) → JSON → TOON Encoder → Main Model
```

El pipeline TOON permite optimizar el uso de tokens al traducir lenguaje natural a un formato compacto (TOON v4.1), reduciendo significativamente el consumo de contexto comparado con el formato JSON estándar. OpenCode delega este procesamiento a un **Python Orchestration Gateway** para resiliencia, health checks y fallback automático.

### Pipeline Detallado

1. **TOON Translator** – OpenCode Subagent que recibe texto en NL (natural language) y lo traduce a JSON estructurado.
2. **Python Orchestration Gateway** – Servicio externo (`scripts/toon/orchestrator.py`) que gestiona el ciclo de vida completo: health checks, comunicación con qwen2.5-3b, codificación TOON y caché.
3. **Main Model** – Recibe el TOON codificado y ejecuta la lógica del framework.

**Ahorro estimado:** 30-50% de tokens vs formato JSON tradicional.

### Orchestrator Gateway

El Orchestrator Gateway es la capa de gestión que delega el procesamiento TOON a un servicio Python externo, proporcionando resiliencia y robustez al pipeline:

- **`orchestrator.py`** – Puerta de enlace externa para gestión del ciclo de vida, health-checks y fallback automático. Coordina todos los sub-componentes TOON en secuencia.
- **`health_checker.py`** – Verifica disponibilidad del servidor qwen2.5-3b (192.168.2.111:8002) con probes HTTP y cache de estado por 30 segundos.
- **`api_gateway.py`** – Maneja la comunicación con el modelo pequeño (qwen2.5-3b) con reintentos automáticos (3 intentos, backoff exponencial, timeout 15s).
- **`cache_manager.py`** – Gestiona caché de resultados en `eitl-artifacts/toon_cache/`, keyed por SHA-256 del input NL, con TTL configurable.

**Comparativa — Direct Call vs Orchestration Gateway:**

| Característica | Direct Call (Old) | Orchestration Gateway (New) |
|----------------|-------------------|-----------------------------|
| **Resiliencia** | Sin protección — fallo del servidor = fallo del pipeline | Health checks + reintentos + fallback automático |
| **Logging** | Mínimo — solo stdout del modelo | Estructurado por componente |
| **Fallback** | No disponible | Caché de resultados, estado UNHEALTHY, error estructurado |
| **Reintentos** | No disponibles | 3 intentos con backoff exponencial |
| **Caché** | No disponible | SHA-256 keyed, TTL configurable |

### Flujo de Datos

```
Usuario (NL)
    ↓
TOON Translator Agent (OpenCode Subagent)
    ↓  CLI Call
orchestrator.py (Python Gateway)
    ├── health_checker.py    (Valida servidor 192.168.2.111:8002)
    ├── api_gateway.py       (Llama a qwen2.5-3b si está healthy)
    ├── to_toon.py           (Codifica JSON → TOON v4.1)
    └── cache_manager.py     (Guarda en eitl-artifacts/toon_cache/)
    ↓  Resultado JSON stdout
Main Model / Scrum Master
```

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
| **toon-translator** | Traductor NL→TOON para optimización de tokens |
| **toon-encoder** | Codifica JSON → TOON v4.1 (scripts/toon/to_toon.py) |
| **toon-decoder** | Decodifica TOON → JSON (scripts/toon/to_json.py) |

## 🚀 Uso Básico

```bash
# Iniciar el pipeline
opencode

# Verificar estado del contexto
context-guard({ action: "check", agent: "auto" })

# Forzar compactación manual (si necesitas)
context-guard({ action: "compact", agent: "auto" })
```

### TOON Commands

- `/toon-translate [NL text]` – Traducir texto en lenguaje natural a TOON (vía Orchestrator Gateway)
- `/toon-stats` – Mostrar estadísticas de ahorro de tokens
- `/toon-health` – Verificar estado del servidor qwen2.5-3b (192.168.2.111:8002)

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
├── scripts/
│   └── toon/
│       ├── orchestrator.py  # Python Orchestration Gateway (ciclo de vida, health, fallback)
│       ├── health_checker.py # Validación de disponibilidad del servidor TOON
│       ├── api_gateway.py   # Comunicación con qwen2.5-3b (reintentos, timeout)
│       ├── to_toon.py      # JSON → TOON encoder
│       ├── to_json.py      # TOON → JSON decoder
│       ├── nl_processor.py  # NL → JSON → TOON pipeline
│       └── requirements.txt
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

*Versión: EitL Framework v3.0 (TOON Layer)*
*Estado: Ready for production use*
