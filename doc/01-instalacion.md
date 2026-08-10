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
| `opencode-kinnycode-memory` | Memoria semantica | Solo si eliges modo memoria |

**Nota**: OpenCode instala los plugins automaticamente al arrancar cuando detecta las referencias en `opencode.jsonc`.

---

## 1.6 Siguiente paso

Una vez instalado, ve a [02 - Inicializar proyecto nuevo](02-inicializar-proyecto-nuevo.md).
