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

[KinnyCodeMemory](https://github.com/kinny1974/kinnyCodeMemory) es un servidor de memoria semantica.

### Instalar

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

### Project ID

El **Project ID** es un identificador unico para tu proyecto.

- **Proyecto nuevo**: el init script genera un ID automaticamente
- **Proyecto existente**: ingresa el ID que ya tienes

### Inicializar

**Modo parametrizado:**
```powershell
# Windows - Proyecto nuevo
.\init-eitl.ps1 -ProjectName "mi-proyecto" -MemoryMode local -MemoryPlugin kinnycode -MemoryUrl "http://localhost:8007"

# Windows - Proyecto existente
.\init-eitl.ps1 -ProjectName "mi-proyecto" -MemoryMode local -MemoryPlugin kinnycode -MemoryUrl "http://localhost:8007" -ProjectId "abc123def456"
```

```bash
# Linux - Proyecto nuevo
./init-eitl.sh "mi-proyecto" local kinnycode "http://localhost:8007"

# Linux - Proyecto existente
./init-eitl.sh "mi-proyecto" local kinnycode "http://localhost:8007" "abc123def456"
```

**Modo interactivo:**
```powershell
.\init-eitl.ps1
```

El script preguntara:
1. Tipo de servidor (KinnyCodeMemory, Mem0, LanceDB)
2. URL del servidor
3. Project ID (solo KinnyCodeMemory)

### Herramientas

| Categoria | Herramientas |
|-----------|--------------|
| Indexacion | `indexar_archivo`, `indexar_proyecto`, `indexar_documento`, `reindexar_archivo` |
| Busqueda | `buscar_codigo`, `buscar_documentos`, `recuperar_contexto` |
| Documentos | `listar_documentos`, `eliminar_documento` |
| Conversaciones | `guardar_conversacion`, `cargar_conversacion`, `guardar_decision` |
| Tareas | `guardar_tarea`, `buscar_tareas` |
| Memoria | `consolidar_memoria`, `contexto_sesion`, `limpiar_proyecto` |

---

## 4.4 Mem0

[Mem0](https://mem0.ai/) es un servicio de memoria conversacional en la nube.

### Inicializar

```powershell
# Windows
.\init-eitl.ps1 -ProjectName "mi-proyecto" -MemoryMode local -MemoryPlugin mem0 -MemoryUrl "http://localhost:8003"
```

```bash
# Linux
./init-eitl.sh "mi-proyecto" local mem0 "http://localhost:8003"
```

### Instalar Mem0

```bash
npx -y mem0-mcp
```

---

## 4.5 LanceDB-OpenCode

[lancedb-opencode-pro](https://github.com/tryweb/lancedb-opencode-pro) es un plugin de memoria local con LanceDB.

### Inicializar

```powershell
# Windows
.\init-eitl.ps1 -ProjectName "mi-proyecto" -MemoryMode local -MemoryPlugin lancedb
```

```bash
# Linux
./init-eitl.sh "mi-proyecto" local lancedb
```

### Configurar

Crear `~/.config/opencode/lancedb-opencode-pro.json`:
```json
{
  "provider": "lancedb-opencode-pro",
  "dbPath": "~/.opencode/memory/lancedb",
  "embedding": {
    "provider": "ollama",
    "model": "nomic-embed-text",
    "baseUrl": "http://127.0.0.1:11434"
  }
}
```

---

## 4.6 Resumen de comandos

| Modo | Comando |
|------|---------|
| Standalone | `.\init-eitl.ps1 -ProjectName "x" -MemoryMode standalone` |
| KinnyCodeMemory (nuevo) | `.\init-eitl.ps1 -ProjectName "x" -MemoryMode local -MemoryPlugin kinnycode -MemoryUrl "http://localhost:8007"` |
| KinnyCodeMemory (existente) | `.\init-eitl.ps1 -ProjectName "x" -MemoryMode local -MemoryPlugin kinnycode -MemoryUrl "http://localhost:8007" -ProjectId "abc123"` |
| Mem0 | `.\init-eitl.ps1 -ProjectName "x" -MemoryMode local -MemoryPlugin mem0 -MemoryUrl "http://localhost:8003"` |
| LanceDB | `.\init-eitl.ps1 -ProjectName "x" -MemoryMode local -MemoryPlugin lancedb` |
