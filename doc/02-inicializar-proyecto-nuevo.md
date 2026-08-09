# 02 · Inicializar un proyecto nuevo

> **Objetivo**: crear un proyecto EitL desde cero, con o sin sistema de memoria, y
> verificar que el pipeline queda listo para recibir el primer requerimiento.

---

## 2.1 Conceptos clave antes de empezar

- El inicializador copia el framework (`.opencode/`) **dentro de tu proyecto** y genera la
  configuración concreta (URLs, API keys, ID de proyecto).
- Los **artefactos del pipeline** se generan en `../eitl-artifacts/` — es decir, en la
  carpeta **hermana** de tu proyecto, no dentro.
- El modo **sin memoria** (standalone) persiste todo en archivos Markdown; el modo
  **con memoria** usa un servidor MCP (KinnyCode, Mem0 o LanceDB). Ver [04 · Memoria](04-memoria.md).

---

## 2.2 Preparación del entorno

### a) Crear la carpeta del proyecto

```bash
# Windows
mkdir C:\Users\<tu-usuario>\projects\mi-proyecto
cd C:\Users\<tu-usuario>\projects\mi-proyecto

# Linux / macOS
mkdir -p ~/projects/mi-proyecto
cd ~/projects/mi-proyecto
```

> ⚠️ **Importante**: la inicialización **siempre se ejecuta desde dentro de la carpeta**
> del proyecto. La carpeta `eitl-artifacts/` se crea en el directorio padre
> (`../eitl-artifacts`).

### b) Definir las variables del entorno (LLM)

EitL necesita una URL de modelo compatible con OpenAI. Dos opciones:

1. **Endpoint local** (llama.cpp, Ollama, vLLM, LM Studio, …) — recomendado para CPU/GPU local.
2. **API remota** (OpenAI, Anthropic, …) — definiendo la URL y API key correspondientes.

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `CPU_BASEURL` | Endpoint base del modelo (CPU) | `http://localhost:11434/v1` |
| `GPU_BASEURL` | Endpoint base del modelo (GPU) | `http://localhost:11434/v1` |
| `API_KEY` | Clave de la API (puede ser `not-needed` en local) | `not-needed` |
| `MEMORY_ENABLED` | Activa/desactiva el MCP de memoria (los scripts ya la leen — T-17) | `false` (default, standalone) |

### c) (Solo memoria) Definir las variables del servidor de memoria

| Variable | Descripción |
|----------|-------------|
| `MEMORY_SERVER_URL` | URL del servidor de memoria MCP (p. ej. `http://127.0.0.1:8005`) |
| `KINYCODE_PATH` (Linux) / `-KinnyCodePath` (Windows) | Ruta de instalación de KinnyCode Memory (contiene `.venv` y `mcp_wrapper.py`) |

---

## 2.3 Modo SIN memoria (standalone)

El modo standalone no requiere servidor de memoria: el estado vive en archivos
`CURRENT_STATE.md`, `TASKS.md` y `DECISIONS.md` dentro de `../eitl-artifacts/`.

### Linux / macOS

```bash
# 1. Exportar variables del LLM (reemplaza por tus valores reales)
export CPU_BASEURL="http://localhost:11434/v1"
export GPU_BASEURL="http://localhost:11434/v1"
export API_KEY="not-needed"
# (opcional) MEMORY_ENABLED=false por defecto; no hace falta exportarla en standalone

# 2. Ejecutar el inicializador
bash ~/tools/eitl-framework/init-scripts/init-eitl.sh "mi-proyecto"
```

### Windows

```powershell
# El script .ps1 recibe los valores como parámetros (no lee variables de entorno)
& "$env:USERPROFILE\Tools\eitl-framework\init-scripts\init-eitl.ps1" `
    -ProjectName "mi-proyecto" `
    -CpuBaseUrl "http://localhost:11434/v1" `
    -GpuBaseUrl "http://localhost:11434/v1" `
    -ApiKey "not-needed"
```

> ✅ **Standalone puro por defecto (T-17 resuelto)**: los scripts ahora **leen
> `MEMORY_ENABLED`** y generan el bloque MCP de KinnyCode con `"enabled": false` si no
> está definida o es `false` (default). Ya **no hace falta editar** `opencode.jsonc` a
> mano. Si dejas el bloque `false` pero el servidor responde, `memory-adapter` ignora el
> MCP deshabilitado y el pipeline opera en modo standalone (persistiendo en archivos).

---

## 2.4 Modo CON memoria

### Opción A — KinnyCode (memoria multiláyer local con LanceDB)

Prerrequisito: tener KinnyCode Memory instalado en la máquina (proporciona `.venv` y
`mcp_wrapper.py`).

```bash
# Linux / macOS
export KINYCODE_PATH="/opt/kinnycode/memory"           # ruta de la instalación
export MEMORY_URL="http://127.0.0.1:8005"              # URL del servidor
export MEMORY_ENABLED=true                             # activa el MCP de memoria
export CPU_BASEURL="http://localhost:11434/v1"
export API_KEY="not-needed"

bash ~/tools/eitl-framework/init-scripts/init-eitl.sh "mi-proyecto"
```

```powershell
# Windows
& "$env:USERPROFILE\Tools\eitl-framework\init-scripts\init-eitl.ps1" `
    -ProjectName "mi-proyecto" `
    -KinnyCodePath "C:\ProgramData\KinnyCode\memory" `
    -MemoryServerUrl "http://127.0.0.1:8005" `
    -MemoryEnabled $true `
    -CpuBaseUrl "http://localhost:11434/v1" `
    -ApiKey "not-needed"
```

El inicializador detecta automáticamente el intérprete de Python del venv de KinnyCode
(`.venv\Scripts\python.exe` en Windows, `.venv/bin/python` en Linux/macOS) y completa la
configuración del MCP con esa ruta y la del wrapper.

### Opción B — Mem0 (memoria conversacional en la nube)

1. Inicializa el proyecto igual que en standalone (sección 2.3).
2. Abre `.opencode/opencode.jsonc` y **reemplaza el bloque `"mcp"`** por la configuración
   de Mem0 (con tu API key):

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

> ℹ️ El comando `npx -y mem0-mcp` viene del README del framework; el nombre de la
> variable `MEM0_API_KEY` corresponde a la documentación oficial de Mem0 — verifícalo
> según la versión del paquete que uses.

### Opción C — LanceDB-OpenCode (plugin nativo)

1. Instala el plugin `lancedb-opencode` desde el marketplace de OpenCode.
2. Añádelo al array `"plugin"` de `.opencode/opencode.jsonc` y a `tui.json`.
3. El nombre del servidor MCP (`lancedb-memory`) es detectado automáticamente por
   `memory-adapter`.

> 📖 Para la detección automática y el orden de prioridad de los backends, ver
> [04 · Memoria](04-memoria.md).

---

## 2.5 Qué genera el inicializador (verificación)

Al terminar, ejecuta el inicializador y comprueba que se generó la estructura esperada:

```
mi-proyecto/
├── .opencode/
│   ├── opencode.jsonc            ← configuración generada (revisa URLs y API key)
│   ├── tui.json
│   ├── agents/  skills/  plugin/  command/  eitl/   ← framework copiado
└── ../eitl-artifacts/            ← carpeta hermana (fuera del proyecto)
    └── CURRENT_STATE.md          ← estado inicial del proyecto
```

El propio script ejecuta una **verificación de estructura** (config principal, TUI,
agentes clave, plugin y skills de QA) y muestra `OK` por cada archivo encontrado.

**Checklist post-inicialización:**

- [ ] `.opencode/opencode.jsonc` existe y las URLs/API key son las correctas
- [ ] `tui.json` existe
- [ ] `../eitl-artifacts/CURRENT_STATE.md` existe con el nombre del proyecto
- [ ] (Con memoria) las rutas del MCP apuntan a archivos que existen
- [ ] (Sin memoria) el bloque MCP está en `"enabled": false` o el servidor no responde
- [ ] `git init` en el proyecto (opcional pero recomendado) y **primer commit** del estado limpio

---

## 2.6 Primer arranque del pipeline

```bash
cd mi-proyecto
opencode
```

En la TUI de OpenCode:

```
/start-SDD "Build a REST API for a todo list app with user authentication"
```

El pipeline ejecuta en orden:

1. **product-owner** → genera `../eitl-artifacts/01_Plan_Scrum.md`
2. **validator** → valida Gate 1 (scrum_plan)
3. **architect** → genera `02_Architecture_SDD.md`
4. **validator** → valida Gate 2 (sdd)
5. **tdd-engineer** → genera `03_Plan_TDD.md`
6. **validator** → valida Gate 3 (tdd_plan)

Si un gate falla, el pipeline se detiene y reintenta (máx. 3 veces) antes de escalar al
humano. Ver [05 · Pipeline y comandos](05-pipeline-y-comandos.md) para la referencia completa.

---

## 2.7 Resumen de la elección con/sin memoria

| Criterio | Sin memoria (standalone) | Con memoria (MCP) |
|----------|--------------------------|--------------------|
| Requisitos extra | Ninguno | Servidor MCP o plugin instalado |
| Persistencia de estado | Archivos Markdown en `../eitl-artifacts/` | Servidor MCP + archivos |
| Memoria entre sesiones | No (se recupera leyendo los archivos) | Sí |
| Velocidad de arranque | Más rápido | Depende del servidor |
| Recomendado para | POCs, demos, proyectos pequeños | Proyectos en curso con contexto largo |

---

**← [01 · Instalación](01-instalacion.md)** · **Siguiente → [03 · Inicializar un proyecto existente](03-inicializar-proyecto-existente.md)**
