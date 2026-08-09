# 06 · Solución de problemas

> **Objetivo**: resolver los problemas más frecuentes de instalación e inicialización y
> conocer las limitaciones conocidas del framework v1.0b, con su mitigación.

---

## 6.1 Problemas frecuentes

| Problema | Causa probable | Solución |
|----------|----------------|----------|
| `context-guard` plugin not found | El plugin no está en el array `plugin` del config | Asegura `"context-guard"` en `opencode.jsonc` → `plugin` |
| Los artefactos no aparecen | Se buscan en el lugar equivocado | Se generan en el **directorio padre**: `ls ../eitl-artifacts/` |
| Ningún endpoint LLM responde | El servidor local no está activo o la URL es incorrecta | Prueba `curl <CPU_BASEURL>/v1/models`; corrige la URL en `opencode.jsonc` |
| El servidor de memoria no conecta | `MEMORY_SERVER_URL` incorrecto o servidor caído | Verifica `MEMORY_SERVER_URL` y que el servidor esté corriendo |
| `init-eitl.ps1` bloqueado por política | Execution Policy de PowerShell | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned` (como admin) |
| El script no encuentra el framework | Bundle incompleto o script movido fuera de `init-scripts/` (la búsqueda es relativa al propio script, no al cwd) | Verifica la estructura descargada: `framework/.opencode/agents/` = 10 y `skills/` = 21; re-descarga el zip si falta algo |
| Verificación del script muestra ERROR | Estructura del bundle incompleta | Re-descarga el zip y comprueba `framework/.opencode/agents/` (10) y `skills/` (21) |
| MCP de memoria da error al abrir OpenCode | Rutas del wrapper/venv no existen (modo standalone) | Pon `"enabled": false` en el bloque `mcp` de `opencode.jsonc`, o instala el servidor |

---

## 6.2 Limitaciones conocidas (1.0b) y mitigaciones

> Estas limitaciones se detectaron durante la auditoría del framework (pruebas unitarias,
> rendimiento y QA). Se listan para que no sean una sorpresa durante el uso.

### L1 · Los scripts de inicialización no leen `MEMORY_ENABLED` (resuelto en 1.0b)

**Resuelto (T-17/M5)**: los init scripts ahora **honran `MEMORY_ENABLED`**:

- `MEMORY_ENABLED=false` (o sin definir) → `mcp.kinnycode-memory` se genera con
  `"enabled": false` (modo standalone por defecto).
- `MEMORY_ENABLED=true` → se genera con `"enabled": true` (con servidor de memoria).

Valores inválidos (`MEMORY_ENABLED=foo`) producen un AVISO y caen a `false`. Ya no hace
falta editar `.opencode/opencode.jsonc` a mano tras inicializar.

### L2 · Valores por defecto con IPs y API key hardcodeadas (resuelto en 1.0b)

**Resuelto**: los init scripts ya **no traen secretos hardcodeados**. Los valores se
resuelven así en ambos scripts:

1. Parámetro explícito (Bash: variables de entorno; PowerShell: `-CpuBaseUrl`, `-ApiKey`, …).
2. Variables de entorno (`CPU_BASEURL`, `GPU_BASEURL`, `API_KEY`, `KINYCODE_PATH`, `MEMORY_URL`).
3. Defaults **no sensibles** y genéricos: `http://localhost:11434/v1` para los endpoints
   y el placeholder `not-needed` para `API_KEY`, con un **AVISO** visible si no definiste
   la clave.

Con ello el bundle puede compartirse o publicarse sin filtrar credenciales de ningún
entorno. Si tu LLM requiere autenticación, exporta/pasa tu `API_KEY` antes de inicializar.

### L3 · Re-inicializar un proyecto con `.opencode` existente genera estructura anidada (resuelto en 1.0b)

**Resuelto (M8/T-21)**: los init scripts ahora hacen **backup + reemplazo** — copian el
`.opencode` existente a `.opencode-backup-<fecha>` y lo eliminan antes de instalar el
framework limpio. Ya no se genera `.opencode/.opencode/`. Verificado por el smoke E2E
(`e2e/smoke-e2e.sh`) y por un check en la CI. Si aún ves anidamiento, es que usas una
versión antigua del bundle: actualiza o repara manualmente con
`mv .opencode/.opencode/* .opencode/ && rmdir .opencode/.opencode`.

### L4 · Plugin `context-guard` — compatibilidad de API (resuelto en 1.0b)

El plugin se migró a la API actual de `@opencode-ai/plugin`: ya no usa el campo `name`,
expone el hook `server` que registra el tool como clave de `Hooks.tool`, resuelve el
agente desde `context.agent` y accede a los datos de sesión de forma **defensiva**
(opcional, por compatibilidad con runtimes que aún los inyectan). Tras la migración,
`npm run typecheck` pasa limpio y las pruebas (45/45) siguen en verde.

### L5 · Salida del plugin dependiente del locale (resuelto en 1.0b)

**Resuelto**: el plugin fija `Intl.NumberFormat("en-US")` para toda su salida numérica
(`formatTokens`) — los tokens y el remaining se muestran siempre con coma (`64,000`),
independientemente del idioma del sistema operativo. La salida es idéntica entre máquinas.

### L6 · Crecimiento O(n²) del estado del context-guard (resuelto en 1.0b)

**Resuelto**: el historial (`alertsSent`/`agentSwitches`) se poda a las últimas **50**
entradas en cada guardado (`saveState`), de modo que la serialización queda acotada y el
coste por `check` es constante. La re-medición confirmó el fix: el batch de 2,000 checks
pasó de 7.2–8.4 s a ~0.2–0.4 s y el p99 de `check` bajó de 6.9–12.1 ms a 4.9–6.1 ms
(la persistencia usa ahora `fs.promises`, con un trade-off medido de ~15–30% menos ops/s
en bench secuencial — detalle en el [07 · QA](07-qa.md) y en
`eitl-artifacts/06_Performance_Report.md`).

### L7 · Nombres de artefactos mixtos español/inglés (resuelto en 1.0b)

**Resuelto (M3/T-15)**: la nomenclatura quedó unificada en inglés — la plantilla ahora se
llama `02_Architecture_SDD.md.template` y el artefacto generado es
`02_Architecture_SDD.md`, igual que el resto del pipeline (`01_Plan_Scrum.md`,
`03_Plan_TDD.md`).

### L8 · `project-config-template/.env.template` (resuelto en 1.0b)

El bundle ahora incluye `project-config-template/.env.template` con las variables
documentadas. Recuerda que los scripts de inicialización leen variables del entorno
(exporta o haz `source` del archivo); no lo auto-cargan.

### L9 · Plantillas y mensajes en español vs. documentación en inglés

Las plantillas de artefactos (`01_Plan_Scrum`, `02_Architecture_SDD`, `03_Plan_TDD`) y
varios mensajes del plugin están en español, aunque 1.0b anuncia contenido en inglés. No
afecta la operación.

### L10 · Ajuste de umbrales del `context-guard` (resuelto en 1.0b)

**Resuelto (L2/T-22)**: antes, `set-threshold` mutaba el perfil compartido `AGENTS` solo
en memoria (el ajuste se perdía al reiniciar). Ahora el umbral por agente se **persiste**
en el estado de la sesión (`thresholdOverrides`). Precedencia: `thresholdOverride` por
llamada > umbral persistido > default del perfil. Coste: `set-threshold` pasa a ser una
escritura real a disco (ver [07 · QA](07-qa.md) y `eitl-artifacts/06`).

---

## 6.3 Checklist de verificación post-inicialización

Ejecuta estos pasos en un proyecto recién inicializado:

```bash
# 1. Estructura del framework
ls .opencode/agents/ | wc -l                        # → 10
ls .opencode/skills/ | wc -l                        # → 21

# 2. Configuración generada
grep -n "enabled" .opencode/opencode.jsonc          # revisa el bloque mcp
grep -n "context-guard" .opencode/opencode.jsonc    # plugin presente

# 3. Artefactos
ls ../eitl-artifacts/                               # CURRENT_STATE.md debe existir

# 4. Endpoint LLM (reemplaza por tu URL)
curl http://localhost:11434/v1/models

# 5. Arranque
opencode
/status                                             # en la TUI: estado Sprint 0
```

---

## 6.4 ¿Sigue sin funcionar?

1. Revisa los logs de OpenCode (modo debug si está disponible).
2. Compara tu estructura con la del capítulo [01 · Instalación](01-instalacion.md).
3. Si es un problema del framework, recuerda que `.opencode/` **no se edita a mano**: se
   corrige en el bundle y se vuelve a inicializar el proyecto.

---

**← [05 · Pipeline y comandos](05-pipeline-y-comandos.md)** · **Siguiente → [07 · QA y auditoría](07-qa.md)**
