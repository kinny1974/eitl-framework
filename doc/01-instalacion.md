# 01 - Instalacion

> **Objetivo**: dejar el framework EitL disponible en tu maquina y verificar que esta
> correctamente instalado antes de inicializar cualquier proyecto.

---

## 1.1 Requisitos previos

| Componente | Version minima | Notas |
|-----------|----------------|-------|
| **OpenCode** | >= 1.4.7 | Debe soportar plugins nativos |
| **Git** | Cualquiera | Para clonar el repositorio |

**Verificacion rapida:**

```bash
# Windows (PowerShell)
git --version
opencode --version

# Linux / macOS
git --version
opencode --version
```

---

## 1.2 Clonar el repositorio

```bash
git clone https://github.com/kinny1974/eitl-framework.git
cd eitl-framework
```

---

## 1.3 Verificar la estructura

```bash
eitl-framework/
|-- framework/                    <- REUTILIZABLE (no editar)
|   +-- .opencode/
|       |-- agents/               <- 10 agentes
|       |-- skills/               <- 21 skills
|       |-- plugin/               <- context-guard.ts
|       +-- eitl/                 <- templates + estado inicial
|-- init-scripts/
|   |-- init-eitl.ps1             <- Windows
|   +-- init-eitl.sh              <- Linux/macOS
|-- doc/                          <- esta documentacion
|-- QUICKSTART.md
+-- README.md
```

---

## 1.4 Windows: politica de ejecucion

Si PowerShell bloquea el script (`init-eitl.ps1`), ejecuta una vez como administrador:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned
```

---

## 1.5 Plugins

El framework usa plugins de OpenCode. La configuracion se genera automaticamente en `opencode.jsonc`.

| Plugin | Proposito | Cuando se instala |
|--------|-----------|-------------------|
| `context-guard` | Monitoreo de contexto | Siempre (incluido en EitL) |

### Plugins de memoria (opcionales)

Si eliges modo memoria en el init script, se configura uno de estos plugins:

| Plugin | Servidor | Almacenamiento |
|--------|----------|----------------|
| `opencode-kinnycode-memory` | KinnyCodeMemory | LanceDB (servidor) |
| `mem0` | Mem0 | Cloud |
| `lancedb-opencode-pro` | LanceDB-OpenCode | LanceDB (local) |

### Instalar plugins manualmente

OpenCode **deberia** instalar los plugins automaticamente al arrancar. Si no lo hace, instala manualmente desde el TUI de OpenCode:

```
/install-plugin opencode-kinnycode-memory
```

Para otros plugins:
```
/install-plugin mem0
/install-plugin lancedb-opencode-pro
```

### Verificar que el plugin se cargo

Despues de instalar, verifica que las herramientas esten disponibles:

```
# En el TUI de OpenCode, ejecuta:
indexar_archivo
```

Si ves las herramientas de memoria, el plugin esta activo.

---

## 1.6 Siguiente paso

Una vez instalado, ve a [02 - Inicializar proyecto nuevo](02-inicializar-proyecto-nuevo.md).

