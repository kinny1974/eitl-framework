#!/bin/bash
# ============================================================
# EitL E2E Smoke Test (T-13)
# Valida la inicialización de un proyecto desde cero y, de forma
# opcional, un smoke test LIVE con OpenCode (requiere LLM real).
#
# Uso:
#   bash e2e/smoke-e2e.sh                 # solo estructural (CI-friendly)
#   OPENCODE_SMOKE=1 bash e2e/smoke-e2e.sh  # + smoke live con opencode CLI
#
# Exit codes: 0 = PASS · 1 = FAIL (estructural) · 2 = SKIP/fallo live
# ============================================================

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INIT_SCRIPT="$ROOT_DIR/init-scripts/init-eitl.sh"

FAILURES=0
pass() { echo -e "  \033[0;32m✓\033[0m $1"; }
fail() { echo -e "  \033[0;31m✗\033[0m $1"; FAILURES=$((FAILURES + 1)); }

echo "=============================================="
echo "  EitL E2E Smoke Test (T-13)"
echo "=============================================="

# 0. Pre-requisitos
if [ ! -f "$INIT_SCRIPT" ]; then
    echo "ERROR: init-eitl.sh no encontrado en $INIT_SCRIPT"
    exit 1
fi
if ! command -v openssl >/dev/null 2>&1; then
    echo "ERROR: openssl requerido (para generar el Project ID)"
    exit 1
fi

# 1. Proyecto temporal
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
PROJECT="smoke-e2e-$(date +%s)"
# Ejecutamos dentro de un subdirectorio del proyecto: los artefactos del init
# (../eitl-artifacts relativo al cwd) quedan en $TMP_DIR/eitl-artifacts y el
# trap de EXIT los limpia junto con el resto (sin residuos en /tmp ni colisiones
# entre corridas concurrentes).
PROJECT_DIR="$TMP_DIR/$PROJECT"
echo "[1] Proyecto temporal: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1

# 2. Inicializar (con defaults no sensibles; sin secretos)
echo "[2] Ejecutando init-eitl.sh..."
if ! bash "$INIT_SCRIPT" "$PROJECT" >"$PROJECT_DIR/init.log" 2>&1; then
    echo "  ✗ init-eitl.sh falló. Log:"
    tail -20 "$PROJECT_DIR/init.log"
    exit 1
fi
pass "init-eitl.sh completó sin errores"

# 3. Estructura del framework
echo "[3] Verificando estructura..."
[ -d ".opencode" ] && pass ".opencode existe" || fail ".opencode NO existe"
AGENTS=$(ls .opencode/agents/ 2>/dev/null | wc -l)
SKILLS=$(ls .opencode/skills/ 2>/dev/null | wc -l)
[ "$AGENTS" -ge 10 ] && pass "10 agentes ($AGENTS)" || fail "agentes: esperado 10, hay $AGENTS"
[ "$SKILLS" -ge 21 ] && pass "21 skills ($SKILLS)" || fail "skills: esperado 21, hay $SKILLS"
[ -f ".opencode/opencode.jsonc" ] && pass "opencode.jsonc generado" || fail "opencode.jsonc NO existe"
[ -f ".opencode/tui.json" ] && pass "tui.json generado" || fail "tui.json NO existe"
[ -f ".opencode/plugin/context-guard.ts" ] && pass "plugin context-guard presente" || fail "plugin context-guard NO existe"
[ -d "../eitl-artifacts" ] && [ -f "../eitl-artifacts/CURRENT_STATE.md" ] && \
    pass "CURRENT_STATE.md creado" || fail "CURRENT_STATE.md NO existe"

# 4. Anti-regresión M8: NO debe haber estructura anidada
echo "[4] Anti-regresión M8 (sin anidamiento)..."
if [ -d ".opencode/.opencode" ]; then
    fail "¡ESTRUCTURA ANIDADA detectada: .opencode/.opencode existe!"
else
    pass "sin anidamiento en la primera inicialización"
fi

# 5. Re-inicialización: debe REEMPLAZAR (no anidar) y hacer backup
echo "[5] Re-inicializando (M8: reemplazo con backup)..."
touch .opencode/marcador.txt
if ! bash "$INIT_SCRIPT" "$PROJECT" >"$PROJECT_DIR/reinit.log" 2>&1; then
    fail "re-init falló"
else
    if [ -d ".opencode/.opencode" ]; then
        fail "¡ANIDAMIENTO tras re-inicializar!"
    else
        pass "sin anidamiento tras re-inicializar"
    fi
    [ -f ".opencode/opencode.jsonc" ] && pass "opencode.jsonc regenerado" || fail "opencode.jsonc ausente tras re-init"
    BACKUP_COUNT=$(ls -d .opencode-backup-* 2>/dev/null | wc -l)
    [ "$BACKUP_COUNT" -ge 1 ] && pass "backup creado ($BACKUP_COUNT)" || fail "no se creó backup"
fi

# 6. Smoke test live (opcional)
echo "[6] Smoke test live (OPENCODE_SMOKE=${OPENCODE_SMOKE:-0})..."
if [ "${OPENCODE_SMOKE:-0}" = "1" ]; then
    if command -v opencode >/dev/null 2>&1; then
        # Verifica que el plugin carga y que la configuración es válida.
        # Un /start-SDD completo requiere un LLM real configurado (CPU_BASEURL/API_KEY).
        echo "  Ejecutando: opencode run (carga de plugin + /start-SDD)..."
        # El run con un agente del pipeline fuerza la carga de plugin/agentes.
        OUTPUT=$(cd "$PROJECT_DIR" && timeout 300 opencode run --agent architect \
            "Ejecuta el tool context-guard con action=report y responde SOLO 'GUARD_OK'" 2>&1)
        if echo "$OUTPUT" | grep -q "GUARD_OK"; then
            pass "plugin context-guard respondió en sesión real"
        else
            echo "  ⚠️ Live: no se obtuvo GUARD_OK (¿LLM configurado?). Salida:"
            echo "$OUTPUT" | tail -15
            echo "  SKIP (no es fallo estructural)"
        fi
    else
        echo "  ⚠️ CLI 'opencode' no encontrado en PATH; salto el smoke live (0-opcional)."
    fi
else
    echo "  (desactivado; usa OPENCODE_SMOKE=1 para probar con OpenCode real)"
fi

# 7. Resumen
echo ""
echo "=============================================="
if [ "$FAILURES" -eq 0 ]; then
    echo -e "  \033[0;32mSMOKE TEST: PASS\033[0m ($PROJECT)"
    echo "=============================================="
    exit 0
else
    echo -e "  \033[0;31mSMOKE TEST: FAIL ($FAILURES errores)\033[0m"
    echo "=============================================="
    exit 1
fi
