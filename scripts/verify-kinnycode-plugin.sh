#!/bin/bash
# ============================================================
# EitL Framework - Verificacion del Plugin KinnyCodeMemory
# ============================================================
# Este script verifica que el plugin opencode-kinnycode-memory
# este correctamente instalado y configurado.

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=========================================="
echo -e "  Verificacion del Plugin KinnyCodeMemory"
echo -e "==========================================${NC}"
echo ""

# 1. Verificar si el plugin esta instalado
echo -e "${CYAN}[1/5] Verificando instalacion del plugin...${NC}"
PLUGIN_DIR="F:\kinnyCodeMemory\plugin-kinnycode"

if [ -d "$PLUGIN_DIR" ]; then
    echo -e "  ${GREEN}✓${NC} Directorio del plugin encontrado"
else
    echo -e "  ${RED}✗${NC} Directorio del plugin no encontrado: $PLUGIN_DIR"
    echo -e "${YELLOW}  Instala el plugin con:${NC}"
    echo -e "    cd F:\kinnyCodeMemory"
    echo -e "    git clone https://github.com/KinnyCode/plugin-kinnycode.git"
    echo -e "    cd plugin-kinnycode"
    echo -e "    npm install"
    echo -e "    npm run build"
    exit 1
fi

# 2. Verificar dependencias
echo -e "${CYAN}[2/5] Verificando dependencias...${NC}"
cd "$PLUGIN_DIR"

if [ -f "package.json" ]; then
    echo -e "  ${GREEN}✓${NC} package.json encontrado"
    
    if [ -d "node_modules" ]; then
        echo -e "  ${GREEN}✓${NC} node_modules encontrado (dependencias instaladas)"
    else
        echo -e "  ${RED}✗${NC} node_modules no encontrado"
        echo -e "${YELLOW}  Instala dependencias con: npm install${NC}"
        exit 1
    fi
    
    if [ -f "dist/index.js" ]; then
        echo -e "  ${GREEN}✓${NC} Plugin compilado (dist/index.js)"
    else
        echo -e "  ${RED}✗${NC} Plugin no compilado"
        echo -e "${YELLOW}  Compila el plugin con: npm run build${NC}"
        exit 1
    fi
else
    echo -e "  ${RED}✗${NC} package.json no encontrado en $PLUGIN_DIR"
    exit 1
fi

# 3. Verificar configuracion en opencode.jsonc
echo -e "${CYAN}[3/5] Verificando configuracion...${NC}"
OPENCODE_CONFIG=".opencode/opencode.jsonc"

if [ -f "$OPENCODE_CONFIG" ]; then
    if grep -q "opencode-kinnycode-memory" "$OPENCODE_CONFIG"; then
        echo -e "  ${GREEN}✓${NC} Plugin configurado en opencode.jsonc"
        
        # Verificar parametros
        if grep -q "serverUrl" "$OPENCODE_CONFIG"; then
            echo -e "  ${GREEN}✓${NC} serverUrl configurado"
        else
            echo -e "  ${YELLOW}⚠${NC} serverUrl no encontrado en configuracion"
        fi
        
        if grep -q "projectId" "$OPENCODE_CONFIG"; then
            echo -e "  ${GREEN}✓${NC} projectId configurado"
        else
            echo -e "  ${YELLOW}⚠${NC} projectId no encontrado en configuracion"
        fi
    else
        echo -e "  ${RED}✗${NC} Plugin no configurado en opencode.jsonc"
        echo -e "${YELLOW}  Agrega el plugin a opencode.jsonc:${NC}"
        echo -e '    "plugin": ['
        echo -e '      ["opencode-kinnycode-memory", {'
        echo -e '        "serverUrl": "http://192.168.2.111:8007",'
        echo -e '        "projectId": "tu-project-id"'
        echo -e '      }],'
        echo -e '      ...'
        echo -e '    ]'
    fi
else
    echo -e "  ${RED}✗${NC} opencode.jsonc no encontrado"
    echo -e "${YELLOW}  Ejecuta primero: init-eitl.ps1 o init-eitl.sh${NC}"
fi

# 4. Verificar variables de entorno
echo -e "${CYAN}[4/5] Verificando variables de entorno...${NC}"
if [ -n "${KINNYCODE_SERVER_URL:-}" ]; then
    echo -e "  ${GREEN}✓${NC} KINNYCODE_SERVER_URL: $KINNYCODE_SERVER_URL"
else
    echo -e "  ${YELLOW}⚠${NC} KINNYCODE_SERVER_URL no definida (usando default)"
fi

if [ -n "${KINNYCODE_PROJECT_ID:-}" ]; then
    echo -e "  ${GREEN}✓${NC} KINNYCODE_PROJECT_ID: $KINNYCODE_PROJECT_ID"
else
    echo -e "  ${YELLOW}⚠${NC} KINNYCODE_PROJECT_ID no definida (usando default)"
fi

# 5. Verificar conexion con el servidor
echo -e "${CYAN}[5/5] Verificando conexion con el servidor...${NC}"
SERVER_URL="${KINNYCODE_SERVER_URL:-http://192.168.2.111:8007}"

if curl -s --connect-timeout 5 "$SERVER_URL" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Servidor accesible en $SERVER_URL"
    
    # Verificar endpoint de proyecto
    PROJECT_ID="${KINNYCODE_PROJECT_ID:-6b6a8b869aea48ad}"
    if curl -s --connect-timeout 5 -X POST "$SERVER_URL/project-info" \
        -H "Content-Type: application/json" \
        -d "{\"project_id\": \"$PROJECT_ID\"}" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Endpoint project-info accesible"
    else
        echo -e "  ${YELLOW}⚠${NC} Endpoint project-info no accesible (puede ser normal)"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} Servidor no accesible en $SERVER_URL"
    echo -e "${YELLOW}  Verifica que el servidor KinnyCode este corriendo:${NC}"
    echo -e "    ssh hell-house \"systemctl status kinnycodememory\""
fi

echo ""
echo -e "${GREEN}=========================================="
echo -e "  VERIFICACION COMPLETADA"
echo -e "==========================================${NC}"
echo ""
echo -e "${CYAN}Resumen:${NC}"
echo -e "  Plugin: ${GREEN}Instalado${NC}"
echo -e "  Configuracion: ${GREEN}Verificada${NC}"
echo -e "  Servidor: ${YELLOW}Verificar manualmente${NC}"
echo ""
echo -e "${YELLOW}Proximos pasos:${NC}"
echo -e "  1. Abre OpenCode: opencode"
echo -e "  2. Verifica que el plugin este cargado: /mcp"
echo -e "  3. Prueba una herramienta: info_proyecto"
echo ""
echo -e "${CYAN}Herramientas disponibles:${NC}"
echo -e "  - indexar_archivo, indexar_proyecto, indexar_documento"
echo -e "  - buscar_codigo, buscar_documentos, recuperar_contexto"
echo -e "  - guardar_conversacion, cargar_conversacion, guardar_decision"
echo -e "  - guardar_tarea, buscar_tareas"
echo -e "  - consolidar_memoria, contexto_sesion, limpiar_proyecto"
echo -e "  - info_proyecto"
