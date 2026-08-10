# 03 - Inicializar un proyecto existente

> **Objetivo**: adjuntar el framework EitL a un proyecto que ya tiene codigo.

---

## 3.1 Cuando tiene sentido

- Quieres aplicar el pipeline de diseno -> TDD -> QA a codigo existente
- Quieres generar artefactos (`01_Plan_Scrum.md`, SDD, TDD, reportes QA)
- Quieres traer memoria de otro proyecto

> El framework **no borra tu codigo fuente**: solo anade `.opencode/` y crea `../eitl-artifacts/`.

---

## 3.2 Precauciones previas

1. **Commit de seguridad**:
   ```bash
   git add -A && git commit -m "chore: snapshot antes de inicializar EitL"
   ```

2. **Verificar si ya existe `.opencode`**:
   ```bash
   ls -la .opencode 2>/dev/null && echo "EXISTE" || echo "No existe"
   ```

---

## 3.3 Procedimiento

### Paso 1 - Navegar al directorio del proyecto

```bash
cd mi-proyecto
```

### Paso 2 - Ejecutar el inicializador

**Modo interactivo:**

```powershell
# Windows
& "F:\eitl-framework\init-scripts\init-eitl.ps1"
```

```bash
# Linux
bash ~/eitl-framework/init-scripts/init-eitl.sh
```

El script preguntara:
1. Nombre del proyecto
2. Modo de memoria (standalone / con servidor)
3. Tipo de plugin (KinnyCodeMemory, Mem0, LanceDB)
4. URL del servidor (si aplica)
5. Project ID (solo KinnyCodeMemory)

El script detectara si ya existe `.opencode` y hara backup automaticamente.

**Modo parametrizado:**

```powershell
# Windows - Standalone
& "F:\eitl-framework\init-scripts\init-eitl.ps1" -ProjectName "mi-proyecto" -MemoryMode standalone

# Windows - KinnyCodeMemory con ID existente
& "F:\eitl-framework\init-scripts\init-eitl.ps1" -ProjectName "mi-proyecto" -MemoryMode local -MemoryPlugin kinnycode -MemoryUrl "http://localhost:8007" -ProjectId "abc123def456"
```

```bash
# Linux - Standalone
bash ~/eitl-framework/init-scripts/init-eitl.sh "mi-proyecto" standalone

# Linux - KinnyCodeMemory con ID existente
bash ~/eitl-framework/init-scripts/init-eitl.sh "mi-proyecto" local kinnycode "http://localhost:8007" "abc123def456"
```

### Paso 3 - Verificar

```bash
ls .opencode/              # Framework copiado
ls ../eitl-artifacts/      # Artefactos creados
```

---

## 3.4 Migrar memoria

Si el proyecto tenia memoria de otro backend:

1. Exporta la memoria actual (si esta disponible)
2. Inicializa con el nuevo modo
3. Importa la memoria

Usa las skills `memory-exporter` e `memory-importer`.

---

## 3.5 Siguiente paso

Ve a [05 - Pipeline y comandos](05-pipeline-y-comandos.md).
