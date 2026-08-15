#Requires -Version 5.1
<#
.SYNOPSIS
    Inicializa un proyecto EitL (Engineering in the Loop) con OpenCode.
.DESCRIPTION
    Configura un proyecto EitL de forma interactiva o parametrizada.
    Sin valores hardcodeados. Memoria OPCIONAL. TOON incluido.
.NOTES
    Version: 1.1.0
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
    Write-Host "  EITL Framework - Inicializador v1.0.2a" -ForegroundColor Cyan
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
# COPIA DE HERRAMIENTAS TOON
# ============================================================================

function Copy-ToolsTOON {
    param([string]$ProjectDir)

    Write-Step "TOON" "Copiando herramientas TOON..."

    $frameworkScriptsDir = Join-Path $PSScriptRoot "..\scripts\toon"
    $targetScriptsDir = Join-Path $ProjectDir "scripts\toon"

    if (-not (Test-Path $frameworkScriptsDir)) {
        Write-Warn "Directorio scripts/toon no encontrado en framework - skipping"
        return
    }

    # Crear directorio destino si no existe
    if (-not (Test-Path $targetScriptsDir)) {
        New-Item -ItemType Directory -Path $targetScriptsDir -Force | Out-Null
    }

    # Copiar archivos TOON
    Copy-Item -Recurse -Force "$frameworkScriptsDir\*" $targetScriptsDir
    Write-Ok "Herramientas TOON copiadas a: scripts/toon/"

    # Copiar agente toon-translator
    $agentSource = Join-Path $PSScriptRoot "..\.opencode\agents\toon-translator.md"
    $agentTarget = Join-Path $ProjectDir ".opencode\agents\toon-translator.md"

    if (Test-Path $agentSource) {
        Copy-Item -Force $agentSource $agentTarget
        Write-Ok "Agente toon-translator copiado"
    }

    # Copiar skill toon-translator
    $skillSource = Join-Path $PSScriptRoot "..\.opencode\skills\toon-translator"
    $skillTarget = Join-Path $ProjectDir ".opencode\skills\toon-translator"

    if (Test-Path $skillSource) {
        if (-not (Test-Path $skillTarget)) {
            New-Item -ItemType Directory -Path $skillTarget -Force | Out-Null
        }
        Copy-Item -Recurse -Force "$skillSource\*" $skillTarget
        Write-Ok "Skill toon-translator copiado"
    }
}

# ============================================================================
# REPARACION AUTOMATICA DE FORMATO DE PERMISOS OBSELETO
# ============================================================================

function Fix-OldPermissions {
    param([string]$ProjectDir)

    Write-Step "FIX" "Verificando formato de permisos en agentes..."

    $agentsDir = Join-Path $ProjectDir ".opencode\agents"
    if (-not (Test-Path $agentsDir)) {
        Write-Warn "Directorio de agentes no encontrado - skipping fix"
        return
    }

    $oldFormatFiles = @()
    foreach ($agentFile in (Get-ChildItem -Path $agentsDir -Filter "*.md")) {
        $content = Get-Content $agentFile -Raw
        if ($content -match '^\s+allow:\s*\[' -or $content -match '^\s+deny:\s*\[') {
            $oldFormatFiles += $agentFile
        }
    }

    if ($oldFormatFiles.Count -eq 0) {
        Write-Ok "Formato de permisos correcto en todos los agentes"
        return
    }

    Write-Warn "Formato de permisos obsoleto detectado en $($oldFormatFiles.Count) archivo(s) - reparando..."

    foreach ($file in $oldFormatFiles) {
        $content = Get-Content $file -Raw
        # Replace old allow/deny array format with correct object format
        # Pattern: bash: then allow: [...] then deny: [...]
        $content = $content -replace '^\s+bash:\s*$', "  bash:`n    `"*`": deny"
        # Replace allow array line
        $content = $content -replace '^\s+allow:\s*\[(.*?)\]', {
            param($match)
            $items = $match.Groups[1].Value -split '\s*,\s*' -replace '"', ''
            $result = @("    `"grep`": allow", "    `"rg`": allow", "    `"find`": allow", "    `"dir`": allow", "    `"Get-ChildItem`": allow", "    `"Get-Content`": allow", "    `"Select-String`": allow", "    `"git`": allow", "    `"npm`": allow", "    `"python`": allow", "    `"pip`": allow", "    `"bandit`": allow", "    `"semgrep`": allow", "    `"nmap`": allow", "    `"sqlmap`": allow", "    `"nikto`": allow", "    `"gitleaks`": allow", "    `"trufflehog`": allow", "    `"snyk`": allow", "    `"npm audit`": allow", "    `"pip-audit`": allow", "    `"safety`": allow", "    `"checkov`": allow", "    `"tfsec`": allow")
            return ($result -join "`n")
        }
        # Remove deny array line (it's already covered by "*": deny)
        $content = $content -replace '^\s+deny:\s*\[(.*?)\]\r?\n?', ''

        $content | Set-Content $file -Encoding UTF8
        Write-Ok "Reparado: $($file.Name)"
    }
}

# ============================================================================
# GENERACION DE CONFIGURACION
# ============================================================================


# ============================================================================
# REPARACION AUTOMATICA DE FORMATO DE PERMISOS OBSELETO
# ============================================================================

function Fix-OldPermissions {
    param([string]$ProjectDir)

    Write-Step "FIX" "Verificando formato de permisos en agentes..."

    $agentsDir = Join-Path $ProjectDir ".opencode\agents"
    if (-not (Test-Path $agentsDir)) {
        Write-Warn "Directorio de agentes no encontrado - skipping fix"
        return
    }

    $oldFormatFiles = @()
    foreach ($agentFile in (Get-ChildItem -Path $agentsDir -Filter "*.md")) {
        $fileContent = Get-Content $agentFile -Raw
        if ($fileContent -match '^\s+allow:\s*\[' -or $fileContent -match '^\s+deny:\s*\[') {
            $oldFormatFiles += $agentFile
        }
    }

    if ($oldFormatFiles.Count -eq 0) {
        Write-Ok "Formato de permisos correcto en todos los agentes"
        return
    }

    Write-Warn "Formato de permisos obsoleto detectado en $($oldFormatFiles.Count) archivo(s) - reparando..."

    foreach ($file in $oldFormatFiles) {
        $fileContent = Get-Content $file -Raw

        $allowedTools = @("grep","rg","find","dir","Get-ChildItem","Get-Content","Select-String","git","npm","python","pip","bandit","semgrep","nmap","sqlmap","nikto","gitleaks","trufflehog","snyk","npm audit","pip-audit","safety","checkov","tfsec")

        $oldPattern = '^\s+bash:\r?\n\s+allow:\s*\[(.*?)\]\r?\n\s+deny:\s*\[(.*?)\]'
        $replacement = "  bash:`n    `"*`": deny"
        foreach ($tool in $allowedTools) {
            $replacement += "`n    `"" + $tool + "`": allow"
        }

        $fileContent = $fileContent -replace $oldPattern, $replacement

        $fileContent | Set-Content $file -Encoding UTF8
        Write-Ok "Reparado: $($file.Name)"
    }
}

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
    $lines += '  "plugin": ['

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
    $lines += '  ],'
    $lines += '  "provider": {'
    $lines += '    "toon-translator": {'
    $lines += '      "name": "TOON Translator (Small Model)",'
    $lines += '      "npm": "@ai-sdk/openai-compatible",'
    $lines += '      "options": {'
    $lines += '        "baseURL": "http://192.168.2.111:8002/v1",'
    $lines += '        "apiKey": "kinny-hellhouse-2026"'
    $lines += '      },'
    $lines += '      "models": {'
    $lines += '        "qwen2.5-3b-instruct": {'
    $lines += '          "name": "qwen2.5-3b-instruct",'
    $lines += '          "contextWindow": 8192,'
    $lines += '          "maxTokens": 2048,'
    $lines += '          "default": true'
    $lines += '        }'
    $lines += '      }'
    $lines += '    }'
    $lines += '  },'
    $lines += '  "agent": {'
    $lines += '    "toon-translator": {'
    $lines += '      "description": "TOON Translator Agent. Orquesta la conversión NL a TOON mediante el orquestador Python (scripts/toon/orchestrator.py).",'
    $lines += '      "mode": "subagent",'
    $lines += '      "prompt": "{file:agents/toon-translator.md}",'
    $lines += '      "permission": {'
    $lines += '        "read": "allow",'
    $lines += '        "edit": "allow",'
    $lines += '        "bash": "ask",'
    $lines += '        "task": "deny",'
    $lines += '        "skill": "allow",'
    $lines += '        "websearch": "deny",'
    $lines += '        "webfetch": "allow",'
    $lines += '        "todowrite": "allow",'
    $lines += '        "todoread": "allow"'
    $lines += '      },'
    $lines += '      "color": "#00BCD4"'
    $lines += '    }'
    $lines += '  }'
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
        @{ P = ".opencode\agents\toon-translator.md"; D = "Agente toon-translator" },
        @{ P = ".opencode\agents\security-agent.md"; D = "Agente security-agent" },
        @{ P = ".opencode\plugin\context-guard.ts"; D = "Plugin context-guard" },
        @{ P = ".opencode\skills\memory-adapter\SKILL.md"; D = "Skill memory-adapter" },
        @{ P = ".opencode\skills\toon-translator\SKILL.md"; D = "Skill toon-translator" },
        @{ P = "scripts\toon\orchestrator.py"; D = "TOON Orchestrator" },
        @{ P = "scripts\toon\api_gateway.py"; D = "TOON API Gateway" },
        @{ P = "scripts\toon\to_toon.py"; D = "TOON Encoder" },
        @{ P = "scripts\toon\to_json.py"; D = "TOON Decoder" }
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

# Detectar si ya estamos dentro de la carpeta del proyecto
Write-Host ""
Write-Step "PROJECT" "Configurando proyecto: $($config.ProjectName)"

$currentDir = Get-Location
$currentDirName = Split-Path $currentDir.Path -Leaf


if ($currentDirName -eq $config.ProjectName) {
    $projectDir = $currentDir.Path
    Write-Ok "Usando directorio actual: $projectDir"
} else {
    $projectDir = Join-Path $currentDir $config.ProjectName
    if (-not (Test-Path $projectDir)) {
        New-Item -ItemType Directory -Path $projectDir | Out-Null
        Write-Ok "Carpeta creada: $projectDir"
    }
}

# Copiar framework
Copy-Framework -ProjectDir $projectDir
Fix-OldPermissions -ProjectDir $projectDir

# Copiar herramientas TOON
Copy-ToolsTOON -ProjectDir $projectDir

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
Write-Host "    .opencode/agents/toon-translator.md" -ForegroundColor Gray
Write-Host "    .opencode/skills/toon-translator/" -ForegroundColor Gray
Write-Host "    scripts/toon/" -ForegroundColor Gray
Write-Host "    ../eitl-artifacts/CURRENT_STATE.md" -ForegroundColor Gray
Write-Host ""
Write-Host "  TOON Layer:" -ForegroundColor Yellow
Write-Host "    - Traductor NL -> TOON v4.1 (30-50% ahorro tokens)" -ForegroundColor Gray
Write-Host "    - Servidor: http://192.168.2.111:8002/v1" -ForegroundColor Gray
Write-Host "    - Uso: @toon-translator Convert to TOON: [requisito]" -ForegroundColor Gray
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





