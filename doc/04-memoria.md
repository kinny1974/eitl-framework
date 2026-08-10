# 04 - Memoria

> **Objetivo**: entender los modos de memoria de EitL (standalone, KinnyCodeMemory, Mem0, LanceDB),
> y como se configuran.

---

## 4.1 Plugins de memoria soportados

| Plugin | Tipo | Almacenamiento | URL Default |
|--------|------|----------------|-------------|
| **kinnycode** | KinnyCodeMemory | LanceDB (servidor) | http://localhost:8007 |
| **mem0** | Mem0 | Cloud | http://localhost:8003 |
| **lancedb** | LanceDB-OpenCode | LanceDB (local) | http://localhost:8007 |
| **Ninguno** | Standalone | Archivos locales | N/A |

---

## 4.2 Standalone (Default)

Sin servidor de memoria. El estado se guarda en `eitl-artifacts/`:

| Archivo | Contenido |
|---------|-----------|
| `CURRENT_STATE.md` | Estado del proyecto |
| `TASKS.md` | Registro de tareas |
| `DECISIONS.md` | Historial de decisiones |

**Ventajas**: cero dependencias, arranque inmediato.

---

## 4.3 KinnyCodeMemory (Recomendado)

[KinnyCodeMemory](https://github.com/kinny1974/kinnyCodeMemory) es un servidor de memoria semantica con 18 herramientas nativas.

### Paso 1: Instalar el servidor

**Opcion A: Binario precompilado**
1. Ir a: https://github.com/kinny1974/kinnyCodeMemory/releases
2. Descargar para tu plataforma
3. Ejecutar:
   ```bash
   # Windows
   .\KinnyCodeMemory-Server.exe

   # Linux
   ./KinnyCodeMemory-Server
   ```

**Opcion B: Desde source**
```bash
git clone https://github.com/kinny1974/kinnyCodeMemory.git
cd kinnyCodeMemory
pip install -r requirements.txt
python memory_server.py
```

### Paso 2: Instalar el plugin de OpenCode

El plugin NO esta en npm. Se instala desde el repositorio:

```bash
# Clonar el repo
git clone --depth 1 https://github.com/kinny1974/kinnyCodeMemory.git
cd kinnyCodeMemory/plugin-kinnycode

# Instalar dependencias y compilar
npm install
npm run build

# Instalar globalmente
npm install -g .
```

### Paso 3: Configurar el init script

```powershell
# Windows
.\init-eitl.ps1 -ProjectName "mi-proyecto" -MemoryMode local -MemoryPlugin kinnycode -MemoryUrl "http://localhost:8007"
```

```bash
# Linux
./init-eitl.sh "mi-proyecto" local kinnycode "http://localhost:8007"
```

### Paso 4: Verificar en OpenCode

```powershell
# Abrir OpenCode
cd mi-proyecto
opencode

# Verificar que el plugin se cargo
/plugins

# Probar una herramienta
indexar_archivo
```

### Project ID

El **Project ID** es un identificador unico para tu proyecto.

- **Proyecto nuevo**: el init script genera un ID automaticamente
- **Proyecto existente**: ingresa el ID que ya tienes

---

## 4.4 API de KinnyCodeMemory

### Endpoints de indexacion

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/index-file` | POST | Indexar archivo con contenido inline |
| `/index-document` | POST | Indexar documento (requiere file_path en servidor) |
| `/remember-decision` | POST | Guardar decision tecnica |
| `/tasks/upsert` | POST | Crear/actualizar tarea |
| `/project-info` | POST | Ver estadisticas del proyecto |
| `/search` | POST | Buscar en la memoria |

### Indexar archivos

```powershell
# Leer contenido del archivo
$content = Get-Content -Path "mi-archivo.py" -Raw -Encoding UTF8

# Construir payload
$body = @{
    project_id = "mi-project-id"
    file_path = "ruta/relativa/mi-archivo.py"
    content = $content
    language = "python"
} | ConvertTo-Json -Depth 5

# Indexar
curl -s -X POST http://localhost:8007/index-file -H "Content-Type: application/json" -d $body
```

**Respuesta exitosa:**
```json
{"status":"success","chunks_indexed":9,"content_hash":"abc123..."}
```

### Registrar decisiones

```powershell
$body = @{
    key_decision = "DEC-001: Arquitectura MVP"
    context = "Se uso patron MVP para separar logica de presentacion"
    project_id = "mi-project-id"
} | ConvertTo-Json -Depth 3

curl -s -X POST http://localhost:8007/remember-decision -H "Content-Type: application/json" -d $body
```

### Registrar tareas

```powershell
$body = @{
    title = "Gate 1: Plan Scrum"
    description = "Plan Scrum con historias y sprints"
    status = "completed"
    priority = "high"
    project_id = "mi-project-id"
} | ConvertTo-Json -Depth 3

curl -s -X POST http://localhost:8007/tasks/upsert -H "Content-Type: application/json" -d $body
```

### Verificar estado

```powershell
curl -s -X POST http://localhost:8007/project-info -H "Content-Type: application/json" -d '{"project_id": "mi-project-id"}'
```

**Respuesta:**
```json
{
  "project_id": "mi-project-id",
  "stats": {
    "code_chunks": 37,
    "document_chunks": 10,
    "conversations": 0,
    "decisions": 5,
    "tasks": 6
  }
}
```

---

## 4.5 Herramientas de KinnyCodeMemory

### Indexacion (4 herramientas)

| Herramienta | Descripcion |
|-------------|-------------|
| `indexar_archivo` | Indexar un archivo de codigo |
| `indexar_proyecto` | Indexar multiples archivos |
| `indexar_documento` | Indexar PDF/MD/TXT |
| `reindexar_archivo` | Re-indexar si cambio el hash |

### Busqueda (3 herramientas)

| Herramienta | Descripcion |
|-------------|-------------|
| `buscar_codigo` | Busqueda semantica en codigo |
| `buscar_documentos` | Buscar en documentos |
| `recuperar_contexto` | RAG completo (todas las capas) |

### Documentos (2 herramientas)

| Herramienta | Descripcion |
|-------------|-------------|
| `listar_documentos` | Listar documentos indexados |
| `eliminar_documento` | Eliminar un documento |

### Conversaciones y decisiones (3 herramientas)

| Herramienta | Descripcion |
|-------------|-------------|
| `guardar_conversacion` | Guardar historial de conversacion |
| `cargar_conversacion` | Recuperar historial |
| `guardar_decision` | Guardar decision tecnica |

### Tareas (2 herramientas)

| Herramienta | Descripcion |
|-------------|-------------|
| `guardar_tarea` | Crear/actualizar tarea (L5) |
| `buscar_tareas` | Busqueda semantica en tareas |

### Memoria (3 herramientas)

| Herramienta | Descripcion |
|-------------|-------------|
| `consolidar_memoria` | Consolidar memoria (eliminar obsoletos) |
| `contexto_sesion` | Contexto proactivo de sesion |
| `limpiar_proyecto` | Eliminar todos los datos del proyecto |

### Proyecto (1 herramienta)

| Herramienta | Descripcion |
|-------------|-------------|
| `info_proyecto` | Estadisticas del proyecto |

---

## 4.6 Mem0

[Mem0](https://mem0.ai/) es un servicio de memoria conversacional en la nube.

### Instalar Mem0

Mem0 es un servicio cloud. Necesitas:

1. **Cuenta en Mem0**: https://mem0.ai
2. **API Key**: Se obtiene desde tu dashboard de Mem0
3. **Servidor MCP**: Ejecutar el servidor local que conecta con la nube

```bash
# Instalar servidor MCP de Mem0
npx -y mem0-mcp

# Configurar API key
export MEM0_API_KEY="tu-api-key-aqui"
```

### Inicializar

```powershell
# Windows
.\init-eitl.ps1 -ProjectName "mi-proyecto" -MemoryMode local -MemoryPlugin mem0 -MemoryUrl "http://localhost:8003"
```

```bash
# Linux
./init-eitl.sh "mi-proyecto" local mem0 "http://localhost:8003"
```

> **Nota**: La URL `http://localhost:8003` es el servidor MCP local que se comunica con la nube de Mem0.

### Limitaciones

- Requiere conexion a internet
- Los datos se almacenan en la nube de Mem0
- Hay un tier gratuito con limites

---

## 4.7 LanceDB-OpenCode

[lancedb-opencode-pro](https://github.com/tryweb/lancedb-opencode-pro) es un plugin de memoria local con LanceDB. **No requiere servidor externo**.

### Prerequisito: Ollama

LanceDB necesita [Ollama](https://ollama.ai/) para generar embeddings:

```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Descargar modelo de embeddings
ollama pull nomic-embed-text
```

### Inicializar

El init script configura automaticamente el plugin:

```powershell
# Windows
.\init-eitl.ps1 -ProjectName "mi-proyecto" -MemoryMode local -MemoryPlugin lancedb
```

```bash
# Linux
./init-eitl.sh "mi-proyecto" local lancedb
```

### Verificar que funciona

```bash
# Verificar que Ollama esta corriendo
curl http://localhost:11434/api/tags

# Verificar que el modelo esta disponible
ollama list
```

---

## 4.8 Resumen de comandos

| Modo | Comando |
|------|---------|
| Standalone | `.\init-eitl.ps1 -ProjectName "x" -MemoryMode standalone` |
| KinnyCodeMemory (nuevo) | `.\init-eitl.ps1 -ProjectName "x" -MemoryMode local -MemoryPlugin kinnycode -MemoryUrl "http://localhost:8007"` |
| KinnyCodeMemory (existente) | `.\init-eitl.ps1 -ProjectName "x" -MemoryMode local -MemoryPlugin kinnycode -MemoryUrl "http://localhost:8007" -ProjectId "abc123"` |
| Mem0 | `.\init-eitl.ps1 -ProjectName "x" -MemoryMode local -MemoryPlugin mem0 -MemoryUrl "http://localhost:8003"` |
| LanceDB | `.\init-eitl.ps1 -ProjectName "x" -MemoryMode local -MemoryPlugin lancedb` |
