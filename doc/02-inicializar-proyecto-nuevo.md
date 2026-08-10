# 02 - Inicializar un proyecto nuevo

> **Objetivo**: crear un proyecto EitL desde cero y verificar que el pipeline queda listo.

---

## 2.1 Conceptos clave

- El inicializador copia el framework (`.opencode/`) dentro de tu proyecto
- Los **artefactos del pipeline** se generan en `../eitl-artifacts/` (carpeta hermana)
- El modo **standalone** es el default (sin servidor de memoria)
- El modo **con memoria** usa un plugin: KinnyCodeMemory, Mem0, o LanceDB

---

## 2.2 Modo interactivo (Recomendado)

### Windows

```powershell
cd F:\eitl-framework\init-scripts
.\init-eitl.ps1
```

### Linux / macOS

```bash
cd ~/eitl-framework/init-scripts
./init-eitl.sh
```

El script preguntara:
1. Nombre del proyecto
2. Modo de memoria (standalone / con servidor)
3. Tipo de plugin (KinnyCodeMemory, Mem0, LanceDB)
4. URL del servidor (si aplica)
5. Project ID (solo KinnyCodeMemory)

---

## 2.3 Modo parametrizado

### Windows

```powershell
# Standalone (sin memoria)
.\init-eitl.ps1 -ProjectName "mi-proyecto" -MemoryMode standalone

# KinnyCodeMemory (proyecto nuevo)
.\init-eitl.ps1 -ProjectName "mi-proyecto" -MemoryMode local -MemoryPlugin kinnycode -MemoryUrl "http://localhost:8007"

# KinnyCodeMemory (proyecto existente con ID)
.\init-eitl.ps1 -ProjectName "mi-proyecto" -MemoryMode local -MemoryPlugin kinnycode -MemoryUrl "http://localhost:8007" -ProjectId "abc123def456"

# Mem0
.\init-eitl.ps1 -ProjectName "mi-proyecto" -MemoryMode local -MemoryPlugin mem0 -MemoryUrl "http://localhost:8003"

# LanceDB
.\init-eitl.ps1 -ProjectName "mi-proyecto" -MemoryMode local -MemoryPlugin lancedb
```

### Linux / macOS

```bash
# Standalone
./init-eitl.sh "mi-proyecto" standalone

# KinnyCodeMemory (proyecto nuevo)
./init-eitl.sh "mi-proyecto" local kinnycode "http://localhost:8007"

# KinnyCodeMemory (proyecto existente con ID)
./init-eitl.sh "mi-proyecto" local kinnycode "http://localhost:8007" "abc123def456"

# Mem0
./init-eitl.sh "mi-proyecto" local mem0 "http://localhost:8003"

# LanceDB
./init-eitl.sh "mi-proyecto" local lancedb
```

---

## 2.4 Verificar la inicializacion

```bash
cd mi-proyecto

# Verificar archivos
ls .opencode/              # Framework copiado
ls ../eitl-artifacts/      # Artefactos creados
cat .opencode/opencode.jsonc  # Configuracion generada
```

---

## 2.5 Arrancar OpenCode

```bash
opencode
```

OpenCode leera `opencode.jsonc` e instalara los plugins automaticamente.

---

## 2.6 Primer pipeline

En el TUI de OpenCode, ejecuta:

```
/start-SDD Build a REST API for user management
```

Esto generara:
- `01_Plan_Scrum.md` -- Planificacion Scrum
- `02_Architecture_SDD.md` -- Diseno de arquitectura
- `03_Plan_TDD.md` -- Plan de pruebas

---

## 2.7 Siguiente paso

Ve a [05 - Pipeline y comandos](05-pipeline-y-comandos.md) para ver todos los comandos disponibles.
