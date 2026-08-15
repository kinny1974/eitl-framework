#!/bin/bash
# ============================================================
# EITL Framework - Inicializador v1.1.0
# Sin valores hardcodeados. Memoria OPCIONAL. TOON incluido.
# https://github.com/kinny1974/eitl-framework
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_DIR="$SCRIPT_DIR/../framework/.opencode"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m'

write_header() {
    echo ""
    echo -e "${CYAN}=============================================${NC}"
    echo -e "${CYAN}  EITL Framework - Inicializador v1.0.1b${NC}"
    echo -e "${GRAY}  https://github.com/kinny1974/eitl-framework${NC}"
    echo -e "${CYAN}=============================================${NC}"
    echo ""
}

write_ok() {
    echo -e "  ${GREEN}[OK]${NC} $1"
}

write_warn() {
    echo -e "  ${YELLOW}[!]${NC} $1"
}

write_err() {
    echo -e "  ${RED}[X]${NC} $1"
}

# ============================================================================
# VALIDACION DE PREREQUISITOS
# ============================================================================

check_prerequisites() {
    echo -e "${CYAN}[PRE] Verificando prerrequisitos...${NC}"

    if command -v git &>/dev/null; then
        write_ok "Git $(git --version | awk '{print $3}')"
    else
        write_err "Git no encontrado - instalar desde: https://git-scm.com/"
        return 1
    fi

    if command -v opencode &>/dev/null; then
        write_ok "OpenCode detectado"
    else
        write_warn "OpenCode no encontrado en PATH"
        echo -e "    ${GRAY}Instalar desde: https://opencode.ai${NC}"
    fi

    return 0
}

# ============================================================================
# MODO INTERACTIVO
# ============================================================================

interactive_config() {
    CONFIG_PROJECT_NAME=""
    CONFIG_MEMORY_MODE=""
    CONFIG_MEMORY_PLUGIN=""
    CONFIG_MEMORY_URL=""
    CONFIG_PROJECT_ID=""

    # Nombre del proyecto
    echo -ne "  Nombre del proyecto: "
    read CONFIG_PROJECT_NAME
    if [ -z "$CONFIG_PROJECT_NAME" ]; then
        write_err "Nombre de proyecto requerido"
        exit 1
    fi

    # Configuracion de memoria
    echo ""
    echo -e "  ${YELLOW}Configuracion de memoria:${NC}"
    echo ""
    echo -e "    ${GREEN}[1]${NC} Standalone (Sin servidor de memoria)"
    echo -e "        ${GRAY}Funciona sin dependencias externas${NC}"
    echo -e "        ${GRAY}Estado se guarda en eitl-artifacts/${NC}"
    echo ""
    echo -e "    ${YELLOW}[2]${NC} Con servidor de memoria"
    echo -e "        ${GRAY}KinnyCodeMemory, Mem0, u otro servidor${NC}"
    echo -e "        ${GRAY}Necesitas el servidor corriendo${NC}"
    echo ""
    echo -ne "  Seleccion [1/2]: "
    read choice

    case $choice in
        1)
            CONFIG_MEMORY_MODE="standalone"
            ;;
        2)
            # Tipo de servidor de memoria
            echo ""
            echo -e "  ${YELLOW}Tipo de servidor de memoria:${NC}"
            echo ""
            echo -e "    ${GREEN}[1]${NC} KinnyCodeMemory (Recomendado)"
            echo -e "    ${YELLOW}[2]${NC} Mem0"
            echo -e "    ${YELLOW}[3]${NC} LanceDB-OpenCode"
            echo ""
            echo -ne "  Seleccion [1/2/3]: "
            read plugin_choice

            case $plugin_choice in
                1) CONFIG_MEMORY_PLUGIN="kinnycode" ;;
                2) CONFIG_MEMORY_PLUGIN="mem0" ;;
                3) CONFIG_MEMORY_PLUGIN="lancedb" ;;
                *)
                    write_err "Seleccion invalida"
                    exit 1
                    ;;
            esac

            # URL del servidor
            echo ""
            if [ "$CONFIG_MEMORY_PLUGIN" = "kinnycode" ]; then
                echo -ne "  URL del servidor KinnyCodeMemory (default: http://localhost:8007): "
            elif [ "$CONFIG_MEMORY_PLUGIN" = "mem0" ]; then
                echo -ne "  URL del servidor Mem0 (default: http://localhost:8003): "
            else
                echo -ne "  URL del servidor: "
            fi
            read url

            # Defaults segun plugin
            if [ -z "$url" ]; then
                case $CONFIG_MEMORY_PLUGIN in
                    kinnycode) url="http://localhost:8007" ;;
                    mem0) url="http://localhost:8003" ;;
                    *) url="http://localhost:8007" ;;
                esac
            fi
            CONFIG_MEMORY_URL="$url"

            # Project ID (solo para KinnyCodeMemory)
            if [ "$CONFIG_MEMORY_PLUGIN" = "kinnycode" ]; then
                echo ""
                echo -e "  ${YELLOW}Project ID:${NC}"
                echo -e "    ${GRAY}Enter = generar nuevo ID${NC}"
                echo -e "    ${GRAY}O escribe el ID existente${NC}"
                echo -ne "  ID: "
                read id
                if [ -z "$id" ]; then
                    CONFIG_PROJECT_ID=$(openssl rand -hex 8 2>/dev/null || cat /dev/urandom | tr -dc 'a-f0-9' | head -c 16)
                else
                    CONFIG_PROJECT_ID="$id"
                fi
            fi

            CONFIG_MEMORY_MODE="local"
            ;;
        *)
            write_err "Seleccion invalida"
            exit 1
            ;;
    esac
}

# ============================================================================
# COPIA DEL FRAMEWORK
# ============================================================================

copy_framework() {
    local project_dir="$1"
    echo -e "${CYAN}[FRAMEWORK] Copiando framework EitL...${NC}"

    if [ ! -d "$FRAMEWORK_DIR" ]; then
        write_err "Framework no encontrado en: $FRAMEWORK_DIR"
        echo -e "    ${GRAY}Ejecuta desde init-scripts/${NC}"
        exit 1
    fi

    local target_dir="$project_dir/.opencode"

    # Backup si existe
    if [ -d "$target_dir" ]; then
        local backup_name=".opencode-backup-$(date +%Y%m%d_%H%M%S)"
        write_warn "Backup de .opencode existente -> $backup_name"
        cp -r "$target_dir" "$project_dir/$backup_name"
        rm -rf "$target_dir"
    fi

    cp -r "$FRAMEWORK_DIR" "$target_dir"
    write_ok "Framework copiado"
}

# ============================================================================
# COPIA DE HERRAMIENTAS TOON
# ============================================================================

copy_toon_tools() {
    local project_dir="$1"
    echo -e "${CYAN}[TOON] Copiando herramientas TOON...${NC}"

    local framework_scripts_dir="$SCRIPT_DIR/../scripts/toon"
    local target_scripts_dir="$project_dir/scripts/toon"

    if [ ! -d "$framework_scripts_dir" ]; then
        write_warn "Directorio scripts/toon no encontrado en framework - skipping"
        return
    fi

    # Crear directorio destino si no existe
    mkdir -p "$target_scripts_dir"

    # Copiar archivos TOON
    cp -r "$framework_scripts_dir"/* "$target_scripts_dir/"
    write_ok "Herramientas TOON copiadas a: scripts/toon/"

    # Copiar agente toon-translator
    local agent_source="$SCRIPT_DIR/../.opencode/agents/toon-translator.md"
    local agent_target="$project_dir/.opencode/agents/toon-translator.md"

    if [ -f "$agent_source" ]; then
        cp -f "$agent_source" "$agent_target"
        write_ok "Agente toon-translator copiado"
    fi

    # Copiar skill toon-translator
    local skill_source="$SCRIPT_DIR/../.opencode/skills/toon-translator"
    local skill_target="$project_dir/.opencode/skills/toon-translator"

    if [ -d "$skill_source" ]; then
        mkdir -p "$skill_target"
        cp -r "$skill_source"/* "$skill_target/"
        write_ok "Skill toon-translator copiado"
    fi
}

# ============================================================================
# GENERACION DE CONFIGURACION
# ============================================================================

generate_config() {
    local project_dir="$1"
    echo -e "${CYAN}[CONFIG] Generando configuracion...${NC}"

    local opencode_dir="$project_dir/.opencode"
    mkdir -p "$opencode_dir"

    local config_path="$opencode_dir/opencode.jsonc"

    # Construir JSON
    {
        echo '{'
        echo '  "$schema": "https://opencode.ai/schema.json",'
        echo '  "plugin": ['

        # Plugin de memoria
        if [ "$CONFIG_MEMORY_MODE" != "standalone" ]; then
            case $CONFIG_MEMORY_PLUGIN in
                kinnycode)
                    echo '    ["opencode-kinnycode-memory", {'
                    echo "      \"serverUrl\": \"$CONFIG_MEMORY_URL\","
                    echo "      \"projectId\": \"$CONFIG_PROJECT_ID\","
                    echo '      "enabled": true'
                    echo '    }],'
                    ;;
                mem0)
                    echo '    "mem0",'
                    ;;
                lancedb)
                    echo '    "lancedb-opencode-pro",'
                    ;;
            esac
        fi

        echo '    "context-guard"'
        echo '  ],'
        echo '  "provider": {'
        echo '    "toon-translator": {'
        echo '      "name": "TOON Translator (Small Model)",'
        echo '      "npm": "@ai-sdk/openai-compatible",'
        echo '      "options": {'
        echo '        "baseURL": "http://192.168.2.111:8002/v1",'
        echo '        "apiKey": "kinny-hellhouse-2026"'
        echo '      },'
        echo '      "models": {'
        echo '        "qwen2.5-3b-instruct": {'
        echo '          "name": "qwen2.5-3b-instruct",'
        echo '          "contextWindow": 8192,'
        echo '          "maxTokens": 2048,'
        echo '          "default": true'
        echo '        }'
        echo '      }'
        echo '    }'
        echo '  },'
        echo '  "agent": {'
        echo '    "toon-translator": {'
        echo '      "description": "TOON Translator Agent. Orquesta la conversión NL a TOON mediante el orquestador Python (scripts/toon/orchestrator.py).",'
        echo '      "mode": "subagent",'
        echo '      "prompt": "{file:agents/toon-translator.md}",'
        echo '      "permission": {'
        echo '        "read": "allow",'
        echo '        "edit": "allow",'
        echo '        "bash": "ask",'
        echo '        "task": "deny",'
        echo '        "skill": "allow",'
        echo '        "websearch": "deny",'
        echo '        "webfetch": "allow",'
        echo '        "todowrite": "allow",'
        echo '        "todoread": "allow"'
        echo '      },'
        echo '      "color": "#00BCD4"'
        echo '    }'
        echo '  }'
        echo '}'
    } > "$config_path"

    write_ok "Configuracion guardada: $config_path"

    # TUI config
    echo '{"theme":"dark"}' > "$opencode_dir/tui.json"
    write_ok "Configuracion TUI guardada"
}

generate_artifacts() {
    local project_dir="$1"
    echo -e "${CYAN}[ARTIFACTS] Creando estructura de artefactos...${NC}"

    local artifacts_dir="$project_dir/../eitl-artifacts"
    mkdir -p "$artifacts_dir"

    local mode_label=""
    local plugin_label=""
    local memory_info=""

    case $CONFIG_MEMORY_MODE in
        standalone)
            mode_label="Standalone (Sin servidor)"
            memory_info="- Modo standalone
- Estado guardado en eitl-artifacts/"
            ;;
        local|remote)
            case $CONFIG_MEMORY_PLUGIN in
                kinnycode)
                    plugin_label="KinnyCodeMemory"
                    memory_info="- Plugin: opencode-kinnycode-memory
- Servidor: $CONFIG_MEMORY_URL
- Project ID: $CONFIG_PROJECT_ID"
                    ;;
                mem0)
                    plugin_label="Mem0"
                    memory_info="- Plugin: mem0
- Servidor: $CONFIG_MEMORY_URL"
                    ;;
                lancedb)
                    plugin_label="LanceDB-OpenCode"
                    memory_info="- Plugin: lancedb-opencode-pro
- Servidor: $CONFIG_MEMORY_URL"
                    ;;
            esac
            mode_label="Servidor $plugin_label"
            ;;
    esac

    cat > "$artifacts_dir/CURRENT_STATE.md" <<EOF
## CURRENT PROJECT STATE

**Proyecto**: $CONFIG_PROJECT_NAME
**Sprint**: 0 - Inicializacion
**Fecha**: $(date +%Y-%m-%d)
**Scrum Master**: ScrumMaster-Agent
**Memory Mode**: $mode_label

### Memory Configuration
$memory_info

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
2. En el TUI: /start-SDD [tu requerimiento]
EOF

    write_ok "Estado inicial creado"
}

# ============================================================================
# VERIFICACION
# ============================================================================

verify_installation() {
    local project_dir="$1"
    echo -e "${CYAN}[VERIFY] Verificando instalacion...${NC}"

    local all_ok=true
    local checks=(
        ".opencode/opencode.jsonc:Config principal"
        ".opencode/tui.json:Config TUI"
        ".opencode/agents/scrum-master.md:Agente scrum-master"
        ".opencode/agents/toon-translator.md:Agente toon-translator"
        ".opencode/plugin/context-guard.ts:Plugin context-guard"
        ".opencode/skills/memory-adapter/SKILL.md:Skill memory-adapter"
        ".opencode/skills/toon-translator/SKILL.md:Skill toon-translator"
        "scripts/toon/orchestrator.py:TOON Orchestrator"
        "scripts/toon/api_gateway.py:TOON API Gateway"
        "scripts/toon/to_toon.py:TOON Encoder"
        "scripts/toon/to_json.py:TOON Decoder"
    )

    for check in "${checks[@]}"; do
        local path="${check%%:*}"
        local desc="${check##*:}"
        if [ -f "$project_dir/$path" ]; then
            write_ok "$desc"
        else
            write_err "$desc - NO ENCONTRADO"
            all_ok=false
        fi
    done

    $all_ok
}

# ============================================================================
# PROGRAMA PRINCIPAL
# ============================================================================

write_header

# Modo parametrizado o interactivo
if [ -n "$1" ] && [ -n "$2" ]; then
    echo -e "  ${GRAY}Modo: Parametrizado${NC}"
    CONFIG_PROJECT_NAME="$1"
    CONFIG_MEMORY_MODE="$2"
    CONFIG_MEMORY_PLUGIN="${3:-kinnycode}"
    CONFIG_MEMORY_URL="${4:-http://localhost:8007}"
    CONFIG_PROJECT_ID="${5:-$(openssl rand -hex 8 2>/dev/null || cat /dev/urandom | tr -dc 'a-f0-9' | head -c 16)}"
else
    echo -e "  ${GRAY}Modo: Interactivo${NC}"
    interactive_config
fi

# Verificar prerrequisitos
echo ""
if ! check_prerequisites; then
    write_err "Faltan prerrequisitos criticos"
    exit 1
fi

# Detectar si ya estamos dentro de la carpeta del proyecto
echo ""
echo -e "${CYAN}[PROJECT] Configurando proyecto: $CONFIG_PROJECT_NAME${NC}"

CURRENT_DIR="$(pwd)"
CURRENT_DIR_NAME="$(basename "$CURRENT_DIR")"

if [ "$CURRENT_DIR_NAME" = "$CONFIG_PROJECT_NAME" ]; then
    PROJECT_DIR="$CURRENT_DIR"
    echo -e "  ${GREEN}[OK]${NC} Usando directorio actual: $PROJECT_DIR"
else
    PROJECT_DIR="$(pwd)/$CONFIG_PROJECT_NAME"
    mkdir -p "$PROJECT_DIR"
    echo -e "  ${GREEN}[OK]${NC} Carpeta creada: $PROJECT_DIR"
fi

# Copiar framework
copy_framework "$PROJECT_DIR"

# Copiar herramientas TOON
copy_toon_tools "$PROJECT_DIR"

# Generar configuracion
generate_config "$PROJECT_DIR"

# Crear artefactos
generate_artifacts "$PROJECT_DIR"

# Verificar
echo ""
verify_installation "$PROJECT_DIR"

# Resumen
case $CONFIG_MEMORY_MODE in
    standalone) MODE_LABEL="Standalone (Sin servidor)" ;;
    local|remote)
        case $CONFIG_MEMORY_PLUGIN in
            kinnycode) PLUGIN_LABEL="KinnyCodeMemory" ;;
            mem0) PLUGIN_LABEL="Mem0" ;;
            lancedb) PLUGIN_LABEL="LanceDB-OpenCode" ;;
        esac
        MODE_LABEL="Servidor $PLUGIN_LABEL"
        ;;
esac

echo ""
echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}  INICIALIZACION COMPLETADA${NC}"
echo -e "${GREEN}=============================================${NC}"
echo ""
echo -e "  Proyecto: ${CYAN}$CONFIG_PROJECT_NAME${NC}"
echo -e "  Memoria: ${CYAN}$MODE_LABEL${NC}"

if [ "$CONFIG_MEMORY_MODE" != "standalone" ]; then
    echo -e "  Plugin: ${CYAN}$PLUGIN_LABEL${NC}"
    echo -e "  Servidor: ${CYAN}$CONFIG_MEMORY_URL${NC}"
    if [ "$CONFIG_MEMORY_PLUGIN" = "kinnycode" ]; then
        echo -e "  Project ID: ${CYAN}$CONFIG_PROJECT_ID${NC}"
    fi
fi

echo ""
echo -e "  ${YELLOW}Archivos generados:${NC}"
echo -e "    .opencode/opencode.jsonc"
echo -e "    .opencode/tui.json"
echo -e "    .opencode/agents/toon-translator.md"
echo -e "    .opencode/skills/toon-translator/"
echo -e "    scripts/toon/"
echo -e "    ../eitl-artifacts/CURRENT_STATE.md"
echo ""
echo -e "  ${YELLOW}TOON Layer:${NC}"
echo -e "    - Traductor NL -> TOON v4.1 (30-50% ahorro tokens)"
echo -e "    - Servidor: http://192.168.2.111:8002/v1"
echo -e "    - Uso: @toon-translator Convert to TOON: [requisito]"
echo ""
echo -e "  ${YELLOW}Siguientes pasos:${NC}"
echo -e "    1. cd $CONFIG_PROJECT_NAME"
echo -e "    2. opencode"
echo -e "    3. /start-SDD [tu requerimiento]"

if [ "$CONFIG_MEMORY_MODE" != "standalone" ]; then
    echo ""
    echo -e "  ${YELLOW}NOTA: Asegurate de que el servidor de memoria este corriendo en:${NC}"
    echo -e "    ${GRAY}$CONFIG_MEMORY_URL${NC}"
fi

echo ""

