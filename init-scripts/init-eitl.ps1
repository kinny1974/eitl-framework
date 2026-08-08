#Requires -Version 5.1
<#
.SYNOPSIS
    Inicializa un nuevo proyecto EitL (Engineering in the Loop) con OpenCode.
.DESCRIPTION
    Genera configuracion de proyecto unica, copia el framework EitL,
    crea directorio de artefactos y prepara todo para iniciar OpenCode.
#>

param(
    [string]$ProjectName = "",
    [string]$KinnyCodePath = "C:\ProgramData\KinnyCode\memory",
    [string]$CpuBaseUrl = "http://192.168.2.111:8002/v1",
    [string]$GpuBaseUrl = "http://192.168.2.111:8001/v1",
    [string]$ApiKey = "kinny-hellhouse-2026",
    [string]$MemoryServerUrl = "http://127.0.0.1:8005"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  EitL Master Bundle - Inicializador" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Nombre del proyecto
if (-not $ProjectName) {
    $ProjectName = Read-Host "Nombre del proyecto (ej: mi-app-eitl)"
    if (-not $ProjectName) {
        Write-Host "ERROR: Nombre de proyecto requerido." -ForegroundColor Red
        exit 1
    }
}

# 2. Generar UUID para KinnyCode
$ProjectId = [guid]::NewGuid().ToString("N").Substring(0, 16)
Write-Host "[1/7] Project ID generado: $ProjectId" -ForegroundColor Green

# 3. Verificar estructura del bundle
$FrameworkDir = Join-Path $PSScriptRoot ".." "framework" ".opencode"
if (-not (Test-Path $FrameworkDir)) {
    Write-Host "ERROR: No se encontro el framework en $FrameworkDir" -ForegroundColor Red
    Write-Host "Asegurate de ejecutar este script desde init-scripts/" -ForegroundColor Yellow
    exit 1
}

# 4. Backup si existe .opencode
if (Test-Path ".opencode") {
    $BackupName = ".opencode-backup-$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "[2/7] Backup de .opencode existente -> $BackupName" -ForegroundColor Yellow
    Copy-Item -Recurse -Force ".opencode" $BackupName
}

# 5. Copiar framework
Write-Host "[3/7] Copiando framework EitL..." -ForegroundColor Cyan
Copy-Item -Recurse -Force $FrameworkDir ".opencode"

# 6. Generar configuracion desde plantilla
$TemplateDir = Join-Path $PSScriptRoot ".." "project-config-template"
$TemplatePath = Join-Path $TemplateDir "opencode.jsonc.template"
$TuiTemplatePath = Join-Path $TemplateDir "tui.json.template"

if (-not (Test-Path $TemplatePath)) {
    Write-Host "ERROR: Plantilla opencode.jsonc.template no encontrada" -ForegroundColor Red
    exit 1
}

Write-Host "[4/7] Generando opencode.jsonc..." -ForegroundColor Cyan
$ConfigContent = Get-Content $TemplatePath -Raw

# Detectar rutas de KinnyCode
$PythonPath = Join-Path $KinnyCodePath ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonPath)) {
    $PythonPath = Join-Path $KinnyCodePath ".venv\bin\python"
}
$WrapperPath = Join-Path $KinnyCodePath "mcp_wrapper.py"

# CORRECCION: Usar .Replace() en vez de -replace para evitar problemas con regex
$ConfigContent = $ConfigContent.Replace('{{KINYCODE_PYTHON_PATH}}', $PythonPath.Replace('\', '\\'))
$ConfigContent = $ConfigContent.Replace('{{KINYCODE_WRAPPER_PATH}}', $WrapperPath.Replace('\', '\\'))
$ConfigContent = $ConfigContent.Replace('{{MEMORY_SERVER_URL}}', $MemoryServerUrl)
$ConfigContent = $ConfigContent.Replace('{{KINNYCODE_PROJECT_ID}}', $ProjectId)
$ConfigContent = $ConfigContent.Replace('{{CPU_BASEURL}}', $CpuBaseUrl)
$ConfigContent = $ConfigContent.Replace('{{GPU_BASEURL}}', $GpuBaseUrl)
$ConfigContent = $ConfigContent.Replace('{{API_KEY}}', $ApiKey)

$ConfigContent | Set-Content ".opencode\opencode.jsonc" -Encoding UTF8

# TUI config
if (Test-Path $TuiTemplatePath) {
    $TuiContent = Get-Content $TuiTemplatePath -Raw
    $TuiContent | Set-Content ".opencode\tui.json" -Encoding UTF8
}

# 7. Crear directorio de artefactos
$ArtifactsDir = "..\eitl-artifacts"
if (-not (Test-Path $ArtifactsDir)) {
    Write-Host "[5/7] Creando directorio de artefactos: $ArtifactsDir" -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $ArtifactsDir | Out-Null
} else {
    Write-Host "[5/7] Directorio de artefactos ya existe: $ArtifactsDir" -ForegroundColor Yellow
}

# 8. Crear initial project state
$StatusPath = Join-Path $ArtifactsDir "CURRENT_STATE.md"
$StatusContent = @"
## CURRENT PROJECT STATE

**Proyecto**: $ProjectName
**Sprint**: 0 - Inicializacion
**Fecha**: $(Get-Date -Format "yyyy-MM-dd")
**Scrum Master**: ScrumMaster-Agent
**KinnyCode Project ID**: $ProjectId

### Generated Artifacts
- [ ] 01_Plan_Scrum.md
- [ ] 02_Arquitectura_SDD.md
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
"@
$StatusContent | Set-Content $StatusPath -Encoding UTF8

# 9. Verificacion
Write-Host "[6/7] Verificando estructura..." -ForegroundColor Cyan
$Checks = @(
    (".opencode\opencode.jsonc", "Config principal"),
    (".opencode\tui.json", "Config TUI"),
    (".opencode\agents\scrum-master.md", "Agente scrum-master"),
    (".opencode\agents\test-runner.md", "Agente test-runner"),
    (".opencode\agents\qa-engineer.md", "Agente qa-engineer"),
    (".opencode\agents\performance-engineer.md", "Agente performance-engineer"),
    (".opencode\plugin\context-guard.ts", "Plugin context-guard"),
    (".opencode\skills\test_execution\SKILL.md", "Skill test_execution"),
    (".opencode\skills\code_quality_gate\SKILL.md", "Skill code_quality_gate"),
    (".opencode\skills\performance_validation\SKILL.md", "Skill performance_validation")
)

$AllOk = $true
foreach ($check in $Checks) {
    $path = $check[0]
    $desc = $check[1]
    if (Test-Path $path) {
        Write-Host "  OK $desc" -ForegroundColor Green
    } else {
        Write-Host "  ERROR $desc NO ENCONTRADO" -ForegroundColor Red
        $AllOk = $false
    }
}

# 10. Resumen
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  INICIALIZACION COMPLETADA" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Proyecto: $ProjectName" -ForegroundColor White
Write-Host "Project ID: $ProjectId" -ForegroundColor White
Write-Host ""
Write-Host "Archivos generados:" -ForegroundColor Cyan
Write-Host "  .opencode/opencode.jsonc" -ForegroundColor Gray
Write-Host "  .opencode/tui.json" -ForegroundColor Gray
Write-Host "  $ArtifactsDir/CURRENT_STATE.md" -ForegroundColor Gray
Write-Host ""
Write-Host "Proximos pasos:" -ForegroundColor Yellow
Write-Host "  1. opencode" -ForegroundColor White
Write-Host "  2. En el TUI: /start-SDD [your requirement]" -ForegroundColor White
Write-Host ""

if (-not $AllOk) {
    Write-Host "ADVERTENCIA: Algunos archivos no se encontraron. Verifica el framework." -ForegroundColor Red
}
