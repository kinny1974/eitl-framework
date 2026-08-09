# 04 · Memoria

> **Objetivo**: entender los modos de memoria de EitL (standalone y servidores MCP),
> cómo se configura cada backend, cómo se auto-detectan y cómo migrar memoria entre
> proyectos.

---

## 4.1 Backends soportados y prioridad de detección

La skill `memory-adapter` actúa como **capa de abstracción**: expone un API unificada
(operaciones `memory_*`) y enruta cada operación al backend detectado según el nombre del
servidor MCP configurado en `opencode.jsonc`.

| Prioridad | Servidor MCP | Tipo | Almacenamiento | Notas |
|-----------|--------------|------|----------------|-------|
| 1 | `kinnycode-memory` | Multiláyer propietario | LanceDB (local) | El stack recomendado por EitL, integración MCP |
| 2 | `mem0` | Memoria conversacional | Cloud | `npx -y mem0-mcp` |
| 3 | `lancedb-opencode` | Plugin nativo de OpenCode | LanceDB (local) | Desde el marketplace de OpenCode |
| 4 | `memory` | Servidor MCP genérico | Cualquiera | Backend estándar |

Si **ningún** backend MCP está disponible, el pipeline opera en **modo standalone**
(sección 4.2).

---

## 4.2 Modo standalone (sin servidor de memoria)

No requiere ningún proceso externo. Todo se persiste en archivos Markdown dentro de
`../eitl-artifacts/`:

| Archivo | Contenido |
|---------|-----------|
| `CURRENT_STATE.md` | Estado del proyecto: sprint, artefactos, backlog, gates, bloqueadores |
| `TASKS.md` | Registro de tareas del pipeline |
| `DECISIONS.md` | Historial de decisiones (append) |

**Ventajas**: cero dependencias, arranque inmediato, fácil de versionar con Git.
**Límites**: no hay búsqueda semántica ni memoria entre sesiones más allá de lo que se
recupera al leer estos archivos al arrancar.

> ✅ **Standalone por defecto (T-17 resuelto)**: los scripts de inicialización ahora leen
> `MEMORY_ENABLED`. Sin definir o `false` → el MCP se genera con `"enabled": false`
> (standalone puro, sin pasos manuales). `true` → `"enabled": true` (con servidor).

---

## 4.3 Configuración por backend

### KinnyCode (prioridad 1)

La configuración la genera el inicializador rellenando la plantilla:

```jsonc
{
  "mcp": {
    "kinnycode-memory": {
      "type": "local",
      "command": [
        "{{KINYCODE_PYTHON_PATH}}",    // python del venv de KinnyCode
        "{{KINYCODE_WRAPPER_PATH}}"    // mcp_wrapper.py
      ],
      "description": "KinnyCode Multi-Layer Memory",
      "environment": {
        "MEMORY_SERVER_URL": "{{MEMORY_SERVER_URL}}",   // p. ej. http://127.0.0.1:8005
        "KINNYCODE_PROJECT_ID": "{{KINNYCODE_PROJECT_ID}}" // 16 hex generado por el script
      },
      "enabled": {{MEMORY_ENABLED}}   // true/false según MEMORY_ENABLED del entorno
    }
  }
}
```

El inicializador detecta el intérprete del venv automáticamente:
- Windows: `<KinnyCodePath>\.venv\Scripts\python.exe`
- Linux/macOS: `<KINYCODE_PATH>/.venv/bin/python`

> 📌 Los placeholders `{{…}}` de la documentación del framework son genéricos
> (`MEMORY_PYTHON_PATH`, `MEMORY_WRAPPER_PATH`, `MEMORY_SERVER_URL`, `PROJECT_ID`,
> `MEMORY_ENABLED`); los scripts concretos usan `KINYCODE_PYTHON_PATH`/`KINYCODE_WRAPPER_PATH`.

### Mem0 (prioridad 2)

Configura el bloque `mcp` con el servidor MCP de Mem0 (ver [02 · Sección 2.4-B](02-inicializar-proyecto-nuevo.md)):

```jsonc
{
  "mcp": {
    "mem0": {
      "type": "local",
      "command": ["npx", "-y", "mem0-mcp"],
      "environment": { "MEM0_API_KEY": "tu-clave-mem0" },
      "enabled": true
    }
  }
}
```

> ℹ️ El comando `npx -y mem0-mcp` está en el README del framework; `MEM0_API_KEY` es el
> nombre usado por la documentación oficial de Mem0 (verifícalo para tu versión).

### LanceDB-OpenCode (prioridad 3)

1. Instala el plugin `lancedb-opencode` (marketplace de OpenCode).
2. Añádelo al array `"plugin"` de `.opencode/opencode.jsonc` y a `tui.json`.
3. El servidor MCP `lancedb-memory` se auto-detecta al arrancar el pipeline.

---

## 4.4 API unificada de memoria (`memory_adapter`)

Independientemente del backend, los agentes usan la misma API:

| Operación | Descripción |
|-----------|-------------|
| `memory_save_state(project_id, state)` | Guarda el estado del proyecto |
| `memory_load_state(project_id)` | Recupera el estado |
| `memory_register_task(...)` | Registra una tarea del pipeline |
| `memory_search(query, n_results, filter_type)` | Búsqueda semántica |
| `memory_export(output_dir, layers)` | Exporta memoria a archivos |
| `memory_import(import_dir, mode)` | Importa memoria (restore/merge) |

---

## 4.5 Capas de memoria (KinnyCode)

La memoria se organiza en 4 capas, exportables de forma selectiva:

| Capa | Contenido |
|------|-----------|
| **C1** | Conversaciones |
| **C2** | Decisiones |
| **C3** | Código indexado |
| **C4** | Documentos |

---

## 4.6 Exportación e importación de memoria

### Exportar (`memory-exporter`)

Genera una carpeta autocontenida con checksums:

```
memory-export_YYYY-MM-DD_HHMMSS/
├── _manifest.json          ← timestamp + versión
├── layer1_conversations/
├── layer2_decisions/
├── layer3_code/
├── layer4_documents/
├── tasks/
└── project_context.md
```

- Export reproducible y con SHA-256 por archivo.
- Soporta exportación selectiva por capa.
- Formato compatible con `memory-importer`.

### Importar (`memory-importer`)

| Parámetro | Valores | Efecto |
|-----------|---------|--------|
| `mode` | `restore` | Reemplazo total |
| `mode` | `merge` | Fusión aditiva (actualizaciones parciales) |

Flujo: valida `_manifest.json` → restaura por capa (reportando conteos) → registra errores
→ verifica checksums cuando existen. **Requiere confirmación** antes de modificar.

---

## 4.7 Portabilidad de proyectos (SIGMA-Team)

`portability-export`/`portability-import` empaquetan el proyecto completo (código,
artefactos, decisiones y configuración de agentes) en rutas relativas con checksums
SHA-256, de modo que cualquier instancia de EitL puede reconstruirlo (ver
[03 · Sección 3.5](03-inicializar-proyecto-existente.md)).

---

## 4.8 Conmutar entre standalone y memoria

### Standalone → Memoria

1. Prepara el servidor MCP (KinnyCode/Mem0/LanceDB) y verifica que responde.
2. Configura el bloque `mcp` en `.opencode/opencode.jsonc` (o vuelve a ejecutar el
   inicializador con las variables de memoria).
3. Si tienes memoria de otro sitio, impórtala con `memory-importer`.
4. Arranca `opencode` — `memory-adapter` detectará el backend y enrutará las operaciones
   `memory_*`.

### Memoria → Standalone

1. Pon `"enabled": false` en el bloque `mcp` (o elimínalo).
2. Exporta tu memoria primero si quieres conservarla: `memory_export(...)`.
3. A partir de ahí, el estado se persiste solo en archivos (`CURRENT_STATE.md`,
   `TASKS.md`, `DECISIONS.md`).

---

**← [03 · Inicializar un proyecto existente](03-inicializar-proyecto-existente.md)** · **Siguiente → [05 · Pipeline y comandos](05-pipeline-y-comandos.md)**
