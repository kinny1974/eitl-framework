# 01 · Instalación

> **Objetivo**: dejar el framework EitL disponible en tu máquina y verificar que está
> correctamente instalado antes de inicializar cualquier proyecto.

---

## 1.1 Requisitos previos

| Componente | Versión mínima | Notas |
|-----------|----------------|-------|
| **OpenCode** | ≥ 1.4.7 | Debe soportar plugins nativos (necesario para `context-guard`). |
| **Node.js** | ≥ 22.6.0 | Requerido por la API de plugins y por el entorno de pruebas. |
| **Python** | ≥ 3.10 | **Opcional** — solo necesario si usarás sistemas de memoria (KinnyCode, etc.). |
| **Git** | Cualquiera | Recomendado para versionar artefactos y poder revertir la inicialización. |
| **PowerShell** | ≥ 5.1 | Solo Windows (para `init-eitl.ps1`). |
| **Bash** | Cualquiera | Solo Linux/macOS (para `init-eitl.sh`). |

**Verificación rápida en la terminal:**

```bash
# Windows (PowerShell)
node --version      # v22.6.0 o superior
git --version
opencode --version  # si opencode está en el PATH

# Linux / macOS (Bash)
node --version
git --version
opencode --version
```

---

## 1.2 Descarga y extracción

### Windows

```powershell
Expand-Archive -Path "eitl-framework-v1.0b.zip" -DestinationPath "$env:USERPROFILE\Tools\eitl-framework"
```

### Linux / macOS

```bash
unzip eitl-framework-v1.0b.zip -d ~/tools/eitl-framework
```

> 💡 El framework se considera **reutilizable**: lo instalas **una sola vez** y desde ahí
> inicializas todos tus proyectos. No es necesario copiarlo dentro de cada proyecto.

---

## 1.3 Verificar la estructura instalada

```bash
eitl-framework/
├── framework/
│   └── .opencode/
│       ├── agents/               ← 10 archivos .md (scrum-master, architect, …)
│       ├── skills/               ← 21 carpetas con SKILL.md
│       ├── plugin/
│       │   ├── context-guard.ts  ← plugin de protección de contexto
│       │   └── vitest.config.ts  ← configuración de pruebas
│       ├── command/              ← comandos TUI
│       └── eitl/
│           └── templates/        ← 3 plantillas de artefactos
├── init-scripts/
│   ├── init-eitl.ps1
│   └── init-eitl.sh
├── project-config-template/
│   ├── opencode.jsonc.template
│   └── tui.json.template
├── QUICKSTART.md
└── README.md
```

**Comprobación manual:**

```bash
# 10 agentes
ls ~/tools/eitl-framework/framework/.opencode/agents/ | wc -l      # → 10

# 21 skills
ls ~/tools/eitl-framework/framework/.opencode/skills/ | wc -l      # → 21
```

---

## 1.4 Windows: política de ejecución de PowerShell

Si PowerShell bloquea el script de inicialización (`init-eitl.ps1`), habilita la política
de ejecución (una sola vez, desde una terminal **como administrador**):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned
```

> `RemoteSigned` permite ejecutar scripts locales sin firma. Puedes usar `Unrestricted`
> si prefieres, pero `RemoteSigned` es el mínimo recomendado.

---

## 1.5 (Opcional) Verificar el framework ejecutando sus pruebas

El plugin `context-guard` incluye un entorno de pruebas con Vitest. Esta verificación es
recomendada para desarrolladores o para validar la instalación en CI:

```bash
cd framework/.opencode/plugin

# 1. Instalar dependencias (la primera vez)
npm install

# 2. Ejecutar pruebas unitarias con cobertura
npm run test:coverage
#   → 30 tests, cobertura del plugin: 100% sentencias / 90% ramas

# 3. (Opcional) Ejecutar benchmarks de rendimiento
npm run bench

# 4. (Opcional) Type-check del plugin
npm run typecheck
```

> ⚠️ Con versiones recientes de `@opencode-ai/plugin` (≥ 1.18), el type-check puede
> reportar errores conocidos de compatibilidad de API (ver [06 · Solución de
> problemas](06-solucion-de-problemas.md), limitación L4). No impide ejecutar las
> pruebas ni los benchmarks.

> ⚠️ Nota: el `package.json`, `node_modules/` y `coverage/` de esta carpeta están en
> `.gitignore` por diseño (el framework no los versiona; se instalan localmente).

---

## 1.6 Siguiente paso

La instalación está completa. Ahora:

- Si vas a crear un **proyecto desde cero** → [02 · Inicializar un proyecto nuevo](02-inicializar-proyecto-nuevo.md)
- Si vas a aplicar EitL a un **proyecto existente** → [03 · Inicializar un proyecto existente](03-inicializar-proyecto-existente.md)

---

**← [Índice del manual](README.md)** · **Siguiente → [02 · Inicializar un proyecto nuevo](02-inicializar-proyecto-nuevo.md)**
