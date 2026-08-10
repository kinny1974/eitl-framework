#Requires -Version 5.1
<#
.SYNOPSIS
    Inicializa un proyecto EitL (Engineering in the Loop) con OpenCode.
.DESCRIPTION
    Configura un proyecto EitL de forma interactiva o parametrizada.
    Sin valores hardcodeados. Memoria OPCIONAL.
.NOTES
    Version: 1.0b
    Repositorio: https://github.com/kinny1974/eitl-framework
#>

param(
    [string]$ProjectName = "",
    [ValidateSet("standalone", "local", "remote")]
    [string]$MemoryMode = "",
    [ValidateSet("kinnycode", "mem0", "lancedb")]
    [string]$MemoryPlugin = "",
    [string]$MemoryUrl = "",
    [string]$ProjectId = "",
    [switch]$NonInteractive
)

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

function Write-Header {
    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "  EITL Framework - Inicializador v1.0b" -ForegroundColor Cyan
    Write-Host "  https://github.com/kinny1974/eitl-framework" -ForegroundColor Gray
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Step, [string]$Message)
    Write-Host "[$Step] $Message" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  [!] $Message" -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Message)
    Write-Host "  [X] $Message" -ForegroundColor Red
}

function Test-CommandExists {
    param([string]$Command)
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

# ============================================================================
# VALIDACION DE PREREQUISITOS
# ============================================================================

function Test-Prerequisites {
    Write-Step "PRE" "Verificando prerrequisitos..."

    if (Test-CommandExists "git") {
        $v = (git --version) -replace 'git version ', ''
        Write-Ok "Git $v"
    } else {
        Write-Err "Git no encontrado - instalar desde: https://git-scm.com/"
        return $false
    }

    if (Test-CommandExists "opencode") {
        Write-Ok "OpenCode detectado"
    } else {
        Write-Warn "OpenCode no encontrado en PATH"
        Write-Host "    Instalar desde: https://opencode.ai" -ForegroundColor Gray
    }

    return $true
}

# ============================================================================
# MENU INTERACTIVO
# ============================================================================

function Get-InteractiveConfig {
    $config = @{}

    # Nombre del proyecto
    Write-Host "  Nombre del proyecto: " -NoNewline -ForegroundColor White
    $config.ProjectName = Read-Host
    if (-not $config.ProjectName) {
        Write-Err "Nombre de proyecto requerido"
        exit 1
    }

    # Configuracion de memoria
    Write-Host ""
    Write-Host "  Configuracion de memoria:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "    [1] Standalone (Sin servidor de memoria)" -ForegroundColor Green
    Write-Host "        Funciona sin ninguna dependencia externa" -ForegroundColor Gray
    Write-Host "        Estado se guarda en eitl-artifacts/" -ForegroundColor Gray
    Write-Host ""
    Write-Host "    [2] Con servidor de memoria" -ForegroundColor Yellow
    Write-Host "        KinnyCodeMemory, Mem0, u otro servidor" -ForegroundColor Gray
    Write-Host "        Necesitas el servidor corriendo" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Seleccion [1/2]: " -NoNewline -ForegroundColor White
    $choice = Read-Host

    switch ($choice) {
        "1" {
            $config.MemoryMode = "standalone"
        }
        "2" {
            # Tipo de servidor de memoria
            Write-Host ""
            Write-Host "  Tipo de servidor de memoria:" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "    [1] KinnyCodeMemory (Recomendado)" -ForegroundColor Green
            Write-Host "    [2] Mem0" -ForegroundColor Yellow
            Write-Host "    [3] LanceDB-OpenCode" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "  Seleccion [1/2/3]: " -NoNewline -ForegroundColor White
            $pluginChoice = Read-Host

            switch ($pluginChoice) {
                "1" { $config.MemoryPlugin = "kinnycode" }
                "2" { $config.MemoryPlugin = "mem0" }
                "3" { $config.MemoryPlugin = "lancedb" }
                default {
                    Write-Err "Seleccion invalida"
                    exit 1
                }
            }

            # URL del servidor
            Write-Host ""
            if ($config.MemoryPlugin -eq "kinnycode") {
                Write-Host "  URL del servidor KinnyCodeMemory (default: http://localhost:8007): " -NoNewline -ForegroundColor White
            } elseif ($config.MemoryPlugin -eq "mem0") {
                Write-Host "  URL del servidor Mem0 (default: http://localhost:8003): " -NoNewline -ForegroundColor White
            } else {
                Write-Host "  URL del servidor: " -NoNewline -ForegroundColor White
            }
            $url = Read-Host

            # Defaults segun plugin
            if (-not $url) {
                switch ($config.MemoryPlugin) {
                    "kinnycode" { $url = "http://localhost:8007" }
                    "mem0" { $url = "http://localhost:8003" }
                    default { $url = "http://localhost:8007" }
                }
            }
            $config.MemoryUrl = $url

            # Project ID (solo para KinnyCodeMemory)
            if ($config.MemoryPlugin -eq "kinnycode") {
                Write-Host ""
                Write-Host "  Project ID:" -ForegroundColor Yellow
                Write-Host "    Enter = generar nuevo ID" -ForegroundColor Gray
                Write-Host "    O escribe el ID existente" -ForegroundColor Gray
                Write-Host "  ID: " -NoNewline -ForegroundColor White
                $id = Read-Host
                $config.ProjectId = if ($id) { $id } else { [guid]::NewGuid().ToString("N").Substring(0, 16) }
            }

            $config.MemoryMode = "local"
        }
        default {
            Write-Err "Seleccion invalida"
            exit 1
        }
    }

    return $config
}

# ============================================================================
# COPIA DEL FRAMEWORK
# ============================================================================

function Copy-Framework {
    param([string]$ProjectDir)

    Write-Step "FRAMEWORK" "Copiando framework EitL..."

    $frameworkDir = Join-Path $PSScriptRoot ".." "framework" ".opencode"
    if (-not (Test-Path $frameworkDir)) {
        Write-Err "Framework no encontrado en: $frameworkDir"
        Write-Host "  Ejecuta este script desde init-scripts/" -ForegroundColor Gray
        exit 1
    }

    $targetDir = Join-Path $ProjectDir ".opencode"

    # Backup si existe
    if (Test-Path $targetDir) {
        $backupName = ".opencode-backup-$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Write-Warn "Backup de .opencode existente -> $backupName"
        Copy-Item -Recurse -Force $targetDir (Join-Path $ProjectDir $backupName)
        Remove-Item -Recurse -Force $targetDir
    }

    Copy-Item -Recurse -Force $frameworkDir $targetDir
    Write-Ok "Framework copiado"
}

# ============================================================================
# GENERACION DE CONFIGURACION
# ============================================================================

function New-ProjectConfig {
    param(
        [string]$ProjectDir,
        [hashtable]$Config
    )

    Write-Step "CONFIG" "Generando configuracion..."

    $opencodeDir = Join-Path $ProjectDir ".opencode"
    if (-not (Test-Path $opencodeDir)) {
        New-Item -ItemType Directory -Path $opencodeDir | Out-Null
    }

    $configPath = Join-Path $opencodeDir "opencode.jsonc"

    # Construir JSON
    $lines = @()
    $lines += '{'
    $lines += '  "$schema": "https://opencode.ai/schema.json",'
    $lines += '  "plugins": ['

    # Plugin de memoria
    if ($Config.MemoryMode -ne "standalone") {
        switch ($Config.MemoryPlugin) {
            "kinnycode" {
                $lines += '    ["opencode-kinnycode-memory", {'
                $lines += "      `"serverUrl`": `"$($Config.MemoryUrl)`","
                $lines += "      `"projectId`": `"$($Config.ProjectId)`","
                $lines += '      "enabled": true'
                $lines += '    }],'
            }
            "mem0" {
                $lines += '    "mem0",'
            }
            "lancedb" {
                $lines += '    "lancedb-opencode-pro",'
            }
        }
    }

    $lines += '    "context-guard"'
    $lines += '  ]'
    $lines += '}'

    $lines -join "`n" | Set-Content $configPath -Encoding UTF8
    Write-Ok "Configuracion guardada: $configPath"

    # TUI config
    $tuiPath = Join-Path $opencodeDir "tui.json"
    '{"theme":"dark"}' | Set-Content $tuiPath -Encoding UTF8
    Write-Ok "Configuracion TUI guardada: $tuiPath"
}

function New-ArtifactsStructure {
    param(
        [string]$ProjectDir,
        [hashtable]$Config
    )

    Write-Step "ARTIFACTS" "Creando estructura de artefactos..."

    $artifactsDir = Join-Path $ProjectDir "..\eitl-artifacts"
    if (-not (Test-Path $artifactsDir)) {
        New-Item -ItemType Directory -Path $artifactsDir | Out-Null
        Write-Ok "Directorio de artefactos creado"
    } else {
        Write-Warn "Directorio de artefactos ya existe"
    }

    $modeLabel = switch ($Config.MemoryMode) {
        "standalone" { "Standalone (Sin servidor)" }
        "local" { "Servidor local" }
        "remote" { "Servidor remoto" }
    }

    $memoryInfo = switch ($Config.MemoryPlugin) {
        "kinnycode" {
            "- Plugin: opencode-kinnycode-memory`n- Servidor: $($Config.MemoryUrl)`n- Project ID: $($Config.ProjectId)"
        }
        "mem0" {
            "- Plugin: mem0`n- Servidor: $($Config.MemoryUrl)"
        }
        "lancedb" {
            "- Plugin: lancedb-opencode-pro`n- Servidor: $($Config.MemoryUrl)"
        }
        default {
            "- Modo standalone`n- Estado guardado en eitl-artifacts/"
        }
    }

    $statePath = Join-Path $artifactsDir "CURRENT_STATE.md"
    @"
## CURRENT PROJECT STATE

**Proyecto**: $($Config.ProjectName)
**Sprint**: 0 - Inicializacion
**Fecha**: $(Get-Date -Format "yyyy-MM-dd")
**Scrum Master**: ScrumMaster-Agent
**Memory Mode**: $modeLabel

### Memory Configuration
$memoryInfo

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
"@ | Set-Content $statePath -Encoding UTF8

    Write-Ok "Estado inicial creado: $statePath"
}

# ============================================================================
# VERIFICACION
# ============================================================================

function Test-Installation {
    param([string]$ProjectDir)

    Write-Step "VERIFY" "Verificando instalacion..."

    $checks = @(
        @{ P = ".opencode\opencode.jsonc"; D = "Config principal" },
        @{ P = ".opencode\tui.json"; D = "Config TUI" },
        @{ P = ".opencode\agents\scrum-master.md"; D = "Agente scrum-master" },
        @{ P = ".opencode\plugin\context-guard.ts"; D = "Plugin context-guard" },
        @{ P = ".opencode\skills\memory-adapter\SKILL.md"; D = "Skill memory-adapter" }
    )

    $allOk = $true
    foreach ($c in $checks) {
        $p = Join-Path $ProjectDir $c.P
        if (Test-Path $p) {
            Write-Ok $c.D
        } else {
            Write-Err "$($c.D) - NO ENCONTRADO"
            $allOk = $false
        }
    }

    return $allOk
}

# ============================================================================
# PROGRAMA PRINCIPAL
# ============================================================================

Write-Header

# Modo interactivo o parametrizado
if ($ProjectName -and $MemoryMode) {
    Write-Host "  Modo: Parametrizado" -ForegroundColor Gray
    $config = @{
        ProjectName = $ProjectName
        MemoryMode  = $MemoryMode
        MemoryPlugin = $MemoryPlugin
        MemoryUrl   = $MemoryUrl
        ProjectId   = if ($ProjectId) { $ProjectId } else { [guid]::NewGuid().ToString("N").Substring(0, 16) }
    }
} else {
    Write-Host "  Modo: Interactivo" -ForegroundColor Gray
    $config = Get-InteractiveConfig
}

# Verificar prerrequisitos
Write-Host ""
if (-not (Test-Prerequisites)) {
    Write-Err "Faltan prerrequisitos criticos"
    exit 1
}

# Crear directorio del proyecto
Write-Host ""
Write-Step "PROJECT" "Creando proyecto: $($config.ProjectName)"

$projectDir = Join-Path (Get-Location) $config.ProjectName
if (-not (Test-Path $projectDir)) {
    New-Item -ItemType Directory -Path $projectDir | Out-Null
}

# Copiar framework
Copy-Framework -ProjectDir $projectDir

# Generar configuracion
New-ProjectConfig -ProjectDir $projectDir -Config $config

# Crear artefactos
New-ArtifactsStructure -ProjectDir $projectDir -Config $config

# Verificar
Write-Host ""
$installOk = Test-Installation -ProjectDir $projectDir

# Resumen
$modeLabel = switch ($config.MemoryMode) {
    "standalone" { "Standalone (Sin servidor)" }
    "local" { "Servidor local" }
    "remote" { "Servidor remoto" }
}

$pluginLabel = switch ($config.MemoryPlugin) {
    "kinnycode" { "KinnyCodeMemory" }
    "mem0" { "Mem0" }
    "lancedb" { "LanceDB-OpenCode" }
    default { "Ninguno" }
}

Write-Host ""
Write-Host "==============================================" -ForegroundColor Green
Write-Host "  INICIALIZACION COMPLETADA" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Proyecto: $($config.ProjectName)" -ForegroundColor Cyan
Write-Host "  Memoria: $modeLabel" -ForegroundColor Cyan

if ($config.MemoryMode -ne "standalone") {
    Write-Host "  Plugin: $pluginLabel" -ForegroundColor Cyan
    Write-Host "  Servidor: $($config.MemoryUrl)" -ForegroundColor Cyan
    if ($config.MemoryPlugin -eq "kinnycode") {
        Write-Host "  Project ID: $($config.ProjectId)" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "  Archivos generados:" -ForegroundColor Yellow
Write-Host "    .opencode/opencode.jsonc" -ForegroundColor Gray
Write-Host "    .opencode/tui.json" -ForegroundColor Gray
Write-Host "    ../eitl-artifacts/CURRENT_STATE.md" -ForegroundColor Gray
Write-Host ""
Write-Host "  Siguientes pasos:" -ForegroundColor Yellow
Write-Host "    1. cd $($config.ProjectName)" -ForegroundColor White
Write-Host "    2. opencode" -ForegroundColor White
Write-Host "    3. /start-SDD [tu requerimiento]" -ForegroundColor White

if ($config.MemoryMode -ne "standalone") {
    Write-Host ""
    Write-Host "  NOTA: Asegurate de que el servidor de memoria este corriendo en:" -ForegroundColor Yellow
    Write-Host "    $($config.MemoryUrl)" -ForegroundColor Gray
}

Write-Host ""

if (-not $installOk) {
    Write-Warn "Algunos archivos no se encontraron. Verifica el framework."
}

