# 03 · Inicializar un proyecto existente

> **Objetivo**: adjuntar el framework EitL a un proyecto que ya tiene código, repositorio
> y posiblemente una configuración propia de `.opencode`, y migrar memoria/estado cuando
> haga falta — con o sin sistema de memoria.

---

## 3.1 ¿Cuándo tiene sentido?

- Quieres aplicar el pipeline de diseño→TDD→QA a un código que ya existe.
- Quieres empezar a generar artefactos (`01_Plan_Scrum.md`, SDD, TDD, reportes QA) para un
  proyecto en curso.
- Tienes memoria de otro proyecto o de otra instancia y quieres traerla.

> ⚠️ El framework **no borra tu código fuente**: solo añade `.opencode/` (framework +
> configuración) y crea `../eitl-artifacts/` con el estado del pipeline. Tu código queda
> intacto.

---

## 3.2 Precauciones previas (obligatorias)

1. **Commit de seguridad**: haz un `git commit` (o stash) para tener el repo limpio y
   poder revertir cualquier cosa.

```bash
git add -A && git commit -m "chore: snapshot antes de inicializar EitL"
```

2. **Comprueba si ya existe `.opencode`**:

```bash
ls -la .opencode 2>/dev/null && echo "EXISTE .opencode" || echo "No existe .opencode"
```

3. **Conoce la ubicación de los artefactos**: el inicializador crea `../eitl-artifacts/`
   en el **directorio padre** del proyecto (donde ejecutas el script), no dentro del repo.
   Si tu proyecto vive en `~/proyectos/mi-app`, los artefactos quedarán en
   `~/proyectos/eitl-artifacts/`. Planifícalo o mueve la carpeta después.

---

## 3.3 Procedimiento paso a paso

> ✅ **M8 resuelto (T-21)**: desde 1.0b los scripts de inicialización **reemplazan** (no
> anidan) un `.opencode` existente: copian el actual a `.opencode-backup-<fecha>` y
> eliminan el original antes de instalar el framework limpio. Ya no se produce la
> estructura anidada `.opencode/.opencode/`.

### Paso 1 — (Opcional) Limpiar una configuración previa de `.opencode`

No es obligatorio: el propio script hace backup + reemplazo automático. Solo si quieres
partir de cero sin conservar backups:

```bash
# Linux / macOS
rm -rf .opencode

# Windows (PowerShell)
Remove-Item -Recurse -Force .opencode
```

> Si tu `.opencode` previo tenía archivos propios (agentes/skills customizados), el backup
> automático `.opencode-backup-<fecha>` los conserva — cópialos de vuelta a `.opencode/`
> tras la inicialización si quieres conservarlos.

### Paso 2 — Definir el entorno (LLM y, opcionalmente, memoria)

Igual que en un proyecto nuevo (ver [02 · Inicializar un proyecto nuevo](02-inicializar-proyecto-nuevo.md)):

```bash
# Linux / macOS — sin memoria
export CPU_BASEURL="http://localhost:11434/v1"
export GPU_BASEURL="http://localhost:11434/v1"
export API_KEY="not-needed"

# Con memoria (KinnyCode), añade también:
export KINYCODE_PATH="/opt/kinnycode/memory"
export MEMORY_URL="http://127.0.0.1:8005"
```

```powershell
# Windows — sin memoria
& "$env:USERPROFILE\Tools\eitl-framework\init-scripts\init-eitl.ps1" `
    -ProjectName "mi-app" `
    -CpuBaseUrl "http://localhost:11434/v1" `
    -GpuBaseUrl "http://localhost:11434/v1" `
    -ApiKey "not-needed"
```

### Paso 3 — Ejecutar el inicializador (desde la raíz del proyecto)

> Si existe un `.opencode` previo, el script lo respalda en `.opencode-backup-<fecha>` y
> lo reemplaza por una copia limpia del framework (M8 resuelto).

```bash
# Linux / macOS
bash ~/tools/eitl-framework/init-scripts/init-eitl.sh "mi-app"

# Windows
& "$env:USERPROFILE\Tools\eitl-framework\init-scripts\init-eitl.ps1" -ProjectName "mi-app"
```

### Paso 4 — Verificar la estructura

```bash
ls .opencode/                     # debe contener agents/, skills/, plugin/, ...
ls ../eitl-artifacts/             # debe contener CURRENT_STATE.md
```

> Si apareciera `.opencode/.opencode/` (por una versión antigua del bundle), repáralo así:

```bash
mv .opencode/.opencode/* .opencode/ && rmdir .opencode/.opencode
```

### Paso 5 — Revisar la configuración generada

```bash
# Revisa que las URLs/API key sean las correctas (los scripts traen valores por defecto
# que debes sobrescribir siempre — ver 06).
cat .opencode/opencode.jsonc
```

- [ ] `baseURL` de `llama-cpp-cpu` y `llama-cpp-gpu` correctos
- [ ] `apiKey` correcta
- [ ] (Sin memoria) bloque `mcp.kinnycode-memory.enabled = false` o servidor no disponible
- [ ] `"context-guard"` presente en el array `plugin`

### Paso 6 — Primer arranque

```bash
opencode
```

En la TUI, el **scrum-master** retoma el estado desde `../eitl-artifacts/CURRENT_STATE.md`
y queda listo para `/start-SDD [requerimiento]`.

---

## 3.4 Con memoria vs sin memoria en un proyecto existente

- **Sin memoria (standalone)**: el estado se persiste en archivos Markdown dentro de
  `../eitl-artifacts/` (`CURRENT_STATE.md`, `TASKS.md`, `DECISIONS.md`). Si ya venías de
  otro proyecto standalone, puedes **copiar esos archivos** a la nueva carpeta de
  artefactos para conservar el historial de decisiones.
- **Con memoria**: configuras un backend (KinnyCode, Mem0 o LanceDB) igual que en un
  proyecto nuevo (ver [04 · Memoria](04-memoria.md)) y, si ya tenías memoria, la importas
  con `memory-importer` (sección siguiente).

---

## 3.5 Migrar estado y memoria entre proyectos

El framework incluye dos mecanismos complementarios:

### a) `memory-exporter` / `memory-importer` (memoria del agente)

Ideal para mover el conocimiento acumulado (conversaciones, decisiones, código indexado,
documentos) de un proyecto a otro o de una instancia a otra.

1. **Exportar** desde el proyecto origen (vía la skill `memory-exporter`):
   genera `memory-export_YYYY-MM-DD_HHMMSS/` con las capas C1–C4, `tasks/` y
   `project_context.md`, más un `_manifest.json` con checksums SHA-256.

2. **Importar** en el proyecto destino (vía la skill `memory-importer`), eligiendo modo:

   | Modo | Comportamiento |
   |------|----------------|
   | `restore` | Reemplaza por completo el estado de memoria actual |
   | `merge` | Fusiona de forma aditiva (solo actualizaciones parciales) |

   La importación **pide confirmación** antes de modificar nada.

### b) `portability-export` / `portability-import` (proyecto completo)

Formato portátil SIGMA-Team: empaqueta artefactos, código y decisiones con verificación
SHA-256 y rutas relativas, de modo que **cualquier instancia de EitL** pueda reconstruir
el proyecto. Útil para mover un proyecto entero entre máquinas/equipos.

```
export/
├── data/
│   ├── artifacts/
│   ├── code/
│   └── decisions/
└── metadata/
    ├── manifest.json
    ├── checksums.sha256
    └── agent-configs/
```

La importación **verifica todos los checksums antes** de reconstruir la estructura.

> 💡 Diferencia práctica: usa `memory-exporter` si solo te interesa el **conocimiento**;
> usa `portability-export` si quieres trasladar el **proyecto completo** (código +
> artefactos + decisiones + configuración de agentes).

---

## 3.6 Checklist final

- [ ] Commit de seguridad realizado
- [ ] Estructura sin `.opencode/.opencode/` (el script reemplaza automáticamente, M8)
- [ ] `opencode.jsonc` generado con URLs/API key correctas
- [ ] `../eitl-artifacts/CURRENT_STATE.md` existe
- [ ] Modo memoria decidido (backend configurado o `enabled: false`)
- [ ] (Si aplica) Memoria importada con `memory-importer` (modo `restore`/`merge`)
- [ ] `opencode` arranca y `/status` muestra el estado del proyecto

---

**← [02 · Inicializar un proyecto nuevo](02-inicializar-proyecto-nuevo.md)** · **Siguiente → [04 · Memoria](04-memoria.md)**
