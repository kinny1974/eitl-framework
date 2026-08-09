#!/bin/bash
# ============================================================
# EitL Master Bundle - Inicializador de Proyecto
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_DIR="$SCRIPT_DIR/../framework/.opencode"
TEMPLATE_DIR="$SCRIPT_DIR/../project-config-template"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=========================================="
echo -e "  EitL Master Bundle - Inicializador"
echo -e "==========================================${NC}"
echo ""

# 1. Nombre del proyecto
if [ -z "$1" ]; then
    read -p "Nombre del proyecto (ej: mi-app-eitl): " PROJECT_NAME
else
    PROJECT_NAME="$1"
fi

if [ -z "$PROJECT_NAME" ]; then
    echo -e "${RED}ERROR: Nombre de proyecto requerido.${NC}"
    exit 1
fi

# 2. Generar UUID para KinnyCode (16 chars hex)
PROJECT_ID=$(openssl rand -hex 8 2>/dev/null || cat /dev/urandom | tr -dc 'a-f0-9' | head -c 16)
echo -e "${GREEN}[1/7] Project ID generado: $PROJECT_ID${NC}"

# 3. Verificar framework
if [ ! -d "$FRAMEWORK_DIR" ]; then
    echo -e "${RED}ERROR: No se encontro el framework en $FRAMEWORK_DIR${NC}"
    echo -e "${YELLOW}Asegurate de ejecutar este script desde init-scripts/${NC}"
    exit 1
fi

# 4. Backup y REEMPLAZO si existe .opencode (M8): el backup se conserva, pero el
#    .opencode existente se elimina antes de copiar el framework para evitar la
#    estructura anidada .opencode/.opencode/ que hacía el pipeline no funcional.
if [ -d ".opencode" ]; then
    BACKUP_NAME=".opencode-backup-$(date +%Y%m%d_%H%M%S)"
    echo -e "${YELLOW}[2/7] Backup de .opencode existente -> $BACKUP_NAME${NC}"
    cp -r .opencode "$BACKUP_NAME"
    echo -e "${YELLOW}      Reemplazando .opencode existente (copia limpia del framework)...${NC}"
    rm -rf .opencode
fi

# 5. Copiar framework
echo -e "${CYAN}[3/7] Copiando framework EitL...${NC}"
cp -r "$FRAMEWORK_DIR" .opencode

# 6. Generar configuracion desde plantilla
if [ ! -f "$TEMPLATE_DIR/opencode.jsonc.template" ]; then
    echo -e "${RED}ERROR: Plantilla opencode.jsonc.template no encontrada${NC}"
    exit 1
fi

echo -e "${CYAN}[4/7] Generando opencode.jsonc...${NC}"

# Configuracion de endpoints (H1/T-10: sin secretos hardcodeados).
# Se leen de variables de entorno; los defaults son NO sensibles y genericos
# (localhost + placeholder) para que el bundle pueda compartirse sin riesgo.
KINYCODE_PATH="${KINYCODE_PATH:-/opt/kinnycode/memory}"
CPU_BASEURL="${CPU_BASEURL:-http://localhost:11434/v1}"
GPU_BASEURL="${GPU_BASEURL:-http://localhost:11434/v1}"
MEMORY_URL="${MEMORY_URL:-http://127.0.0.1:8005}"
# Memoria (M5/T-17): los scripts ahora HONRAN MEMORY_ENABLED. Default "false"
# (standalone, sin servidor de memoria) coherente con .env.template/README.
# MEMORY_ENABLED=true genera el MCP de KinnyCode con "enabled": true.
MEMORY_ENABLED="${MEMORY_ENABLED:-false}"
# Normalizar a minusculas (acepta TRUE/True/1/yes, coherente con el fix de PS1)
MEMORY_ENABLED=$(echo "$MEMORY_ENABLED" | tr '[:upper:]' '[:lower:]')
if [ "$MEMORY_ENABLED" != "true" ] && [ "$MEMORY_ENABLED" != "false" ]; then
    echo -e "${YELLOW}AVISO: MEMORY_ENABLED='$MEMORY_ENABLED' no reconocido; se usara 'false'.${NC}"
    MEMORY_ENABLED="false"
fi

# AVISO solo si API_KEY no se definio (ni siquiera como placeholder): comprobar
# ANTES de aplicar el default evita el falso positivo cuando el usuario exporta
# API_KEY=not-needed a proposito (guia oficial para LLM local).
if [ -z "${API_KEY:-}" ]; then
    echo -e "${YELLOW}AVISO: API_KEY no definida; se usara el placeholder 'not-needed'.${NC}"
    echo -e "${YELLOW}  Exporta API_KEY (y opcionalmente CPU_BASEURL/GPU_BASEURL) antes de ejecutar.${NC}"
fi
API_KEY="${API_KEY:-not-needed}"

# Python path (intentar detectar venv)
if [ -f "$KINYCODE_PATH/.venv/bin/python" ]; then
    PYTHON_PATH="$KINYCODE_PATH/.venv/bin/python"
elif [ -f "$KINYCODE_PATH/.venv/Scripts/python.exe" ]; then
    PYTHON_PATH="$KINYCODE_PATH/.venv/Scripts/python.exe"
else
    PYTHON_PATH="python3"
fi

WRAPPER_PATH="$KINYCODE_PATH/mcp_wrapper.py"

# Reemplazar placeholders
sed -e "s|{{KINYCODE_PYTHON_PATH}}|$PYTHON_PATH|g"     -e "s|{{KINYCODE_WRAPPER_PATH}}|$WRAPPER_PATH|g"     -e "s|{{MEMORY_SERVER_URL}}|$MEMORY_URL|g"     -e "s|{{KINNYCODE_PROJECT_ID}}|$PROJECT_ID|g"     -e "s|{{CPU_BASEURL}}|$CPU_BASEURL|g"     -e "s|{{GPU_BASEURL}}|$GPU_BASEURL|g"     -e "s|{{API_KEY}}|$API_KEY|g"     -e "s|{{MEMORY_ENABLED}}|$MEMORY_ENABLED|g"     "$TEMPLATE_DIR/opencode.jsonc.template" > .opencode/opencode.jsonc

# TUI config
cp "$TEMPLATE_DIR/tui.json.template" .opencode/tui.json

# 7. Crear directorio de artefactos
ARTIFACTS_DIR="../eitl-artifacts"
if [ ! -d "$ARTIFACTS_DIR" ]; then
    echo -e "${CYAN}[5/7] Creando directorio de artefactos: $ARTIFACTS_DIR${NC}"
    mkdir -p "$ARTIFACTS_DIR"
else
    echo -e "${YELLOW}[5/7] Directorio de artefactos ya existe: $ARTIFACTS_DIR${NC}"
fi

# 8. Crear initial state
ESTADO_PATH="$ARTIFACTS_DIR/CURRENT_STATE.md"
cat > "$ESTADO_PATH" <<EOF
## CURRENT PROJECT STATE

**Proyecto**: $PROJECT_NAME
**Sprint**: 0 - Inicializacion
**Fecha**: $(date +%Y-%m-%d)
**Scrum Master**: ScrumMaster-Agent
**KinnyCode Project ID**: $PROJECT_ID

### Generated Artifacts
- [ ] 01_Plan_Scrum.md
- [ ] 02_Architecture_SDD.md
- [ ] 03_Plan_TDD.md
- [ ] 04_Test_Report.md
- [ ] 05_QA_Report.md
- [ ] 06_Performance_Report.md
- [ ] Code Implementation
- [ ] Tests Executed

### Sprint Backlog
- [x] Inicializar pipeline EitL
- [ ] Recibir requerimiento del cliente
- [ ] Run /start-SDD

### Gates
| Gate | Status | Retry |
|------|--------|-------|
| Gate 1 (scrum_plan) | Pending | 0/3 |
| Gate 2 (sdd) | Pending | 0/3 |
| Gate 3 (tdd_plan) | Pending | 0/3 |
| Gate 4 (tests) | Pending | 0/3 |
| Gate 5 (qa) | Pending | 0/3 |
| Gate 6 (performance) | Pending | 0/3 |

### Blockers
- None

### Next Steps
1. Ejecutar: opencode
2. En el TUI: /start-SDD [your requirement]
EOF

# 9. Verificacion
echo -e "${CYAN}[6/7] Verificando estructura...${NC}"
CHECKS=(
    ".opencode/opencode.jsonc:Config principal"
    ".opencode/tui.json:Config TUI"
    ".opencode/agents/scrum-master.md:Agente scrum-master"
    ".opencode/agents/test-runner.md:Agente test-runner"
    ".opencode/agents/qa-engineer.md:Agente qa-engineer"
    ".opencode/agents/performance-engineer.md:Agente performance-engineer"
    ".opencode/plugin/context-guard.ts:Plugin context-guard"
    ".opencode/skills/test_execution/SKILL.md:Skill test_execution"
    ".opencode/skills/code_quality_gate/SKILL.md:Skill code_quality_gate"
    ".opencode/skills/performance_validation/SKILL.md:Skill performance_validation"
)

ALL_OK=true
for check in "${CHECKS[@]}"; do
    path="${check%%:*}"
    desc="${check##*:}"
    if [ -f "$path" ] || [ -d "$path" ]; then
        echo -e "  ${GREEN}✓${NC} $desc"
    else
        echo -e "  ${RED}✗${NC} $desc NO ENCONTRADO"
        ALL_OK=false
    fi
done

# 10. Resumen
echo ""
echo -e "${GREEN}=========================================="
echo -e "  INICIALIZACION COMPLETADA"
echo -e "==========================================${NC}"
echo -e "Proyecto: ${CYAN}$PROJECT_NAME${NC}"
echo -e "Project ID: ${CYAN}$PROJECT_ID${NC}"
echo ""
echo -e "${CYAN}Archivos generados:${NC}"
echo -e "  .opencode/opencode.jsonc"
echo -e "  .opencode/tui.json"
echo -e "  $ARTIFACTS_DIR/CURRENT_STATE.md"
echo ""
echo -e "${YELLOW}Proximos pasos:${NC}"
echo -e "  1. ${WHITE}opencode${NC}"
echo -e "  2. En el TUI: ${WHITE}/start-SDD [your requirement]${NC}"
echo ""

if [ "$ALL_OK" = false ]; then
    echo -e "${RED}ADVERTENCIA: Algunos archivos no se encontraron. Verifica el framework.${NC}"
fi
