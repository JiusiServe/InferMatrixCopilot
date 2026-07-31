[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("codex", "claude", "cursor")]
    [string]$Agent,

    [string]$ConfigRoot = [Environment]::GetFolderPath("UserProfile"),

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonPath = Join-Path $ProjectRoot "src"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$SkillRoot = Join-Path $ProjectRoot "plugin\skills"

function Find-CompatiblePython {
    $Candidates = @()

    if (Get-Command py -ErrorAction SilentlyContinue) {
        $PreviousPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $LauncherOutput = & py -0p 2>$null
        $ErrorActionPreference = $PreviousPreference
        $LauncherOutput | ForEach-Object {
            if ($_ -match '^\s*-\S+\s+\*?\s*(.+?)\s*$') {
                $Candidates += $Matches[1].Trim().Trim('"')
            }
        }
    }

    foreach ($Name in @("python", "python3")) {
        $Resolved = Get-Command $Name -ErrorAction SilentlyContinue
        if ($Resolved) {
            $Candidates += $Resolved.Source
        }
    }

    foreach ($Candidate in $Candidates | Select-Object -Unique) {
        if (-not (Test-Path -LiteralPath $Candidate) -and
            -not (Get-Command $Candidate -ErrorAction SilentlyContinue)) {
            continue
        }
        & $Candidate -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $Candidate
        }
    }

    throw "No compatible Python found. Install Python 3.11 or newer."
}

function Install-AgentSkills([string]$DestinationRoot) {
    New-Item -ItemType Directory -Force -Path $DestinationRoot | Out-Null
    Get-ChildItem -LiteralPath $SkillRoot -Directory | ForEach-Object {
        $Destination = Join-Path $DestinationRoot $_.Name
        New-Item -ItemType Directory -Force -Path $Destination | Out-Null
        Get-ChildItem -LiteralPath $_.FullName -Force | ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination $Destination `
                -Recurse -Force
        }
        Get-ChildItem -LiteralPath $Destination -File -Recurse | ForEach-Object {
            $Content = Get-Content -Raw -LiteralPath $_.FullName
            if ($Content.Contains("{{INFERMATRIX_COPILOT_ROOT}}")) {
                $Content = $Content.Replace(
                    "{{INFERMATRIX_COPILOT_ROOT}}",
                    $ProjectRoot
                )
                [IO.File]::WriteAllText(
                    $_.FullName,
                    $Content,
                    (New-Object Text.UTF8Encoding($false))
                )
            }
        }
    }
}

function Remove-McpRegistration([string]$Command, [string[]]$Arguments) {
    $PreviousPreference = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    & $Command @Arguments 2>$null | Out-Null
    $ErrorActionPreference = $PreviousPreference
}

function Install-CursorConfig {
    $CursorRoot = Join-Path $ConfigRoot ".cursor"
    $ConfigPath = Join-Path $CursorRoot "mcp.json"
    New-Item -ItemType Directory -Force -Path $CursorRoot | Out-Null

    if (Test-Path -LiteralPath $ConfigPath) {
        try {
            $Config = Get-Content -Raw -LiteralPath $ConfigPath | ConvertFrom-Json
        }
        catch {
            throw "Cursor config is not valid JSON and was not changed: $ConfigPath"
        }
        $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        Copy-Item -LiteralPath $ConfigPath -Destination "$ConfigPath.$Timestamp.bak"
    }
    else {
        $Config = [pscustomobject]@{}
    }

    if (-not $Config.PSObject.Properties["mcpServers"]) {
        $Config | Add-Member -NotePropertyName "mcpServers" `
            -NotePropertyValue ([pscustomobject]@{})
    }
    elseif ($null -eq $Config.mcpServers) {
        $Config.mcpServers = [pscustomobject]@{}
    }

    $Server = [pscustomobject]@{
        command = $VenvPython
        args = @("-m", "infermatrix_copilot.thin_mcp_server")
        env = [pscustomobject]@{ PYTHONPATH = $PythonPath }
    }

    if ($Config.mcpServers.PSObject.Properties["infermatrix_copilot"]) {
        $Config.mcpServers.infermatrix_copilot = $Server
    }
    else {
        $Config.mcpServers | Add-Member `
            -NotePropertyName "infermatrix_copilot" `
            -NotePropertyValue $Server
    }

    $Json = $Config | ConvertTo-Json -Depth 20
    [IO.File]::WriteAllText(
        $ConfigPath,
        $Json + [Environment]::NewLine,
        (New-Object Text.UTF8Encoding($false))
    )

    $CommandRoot = Join-Path $CursorRoot "commands"
    New-Item -ItemType Directory -Force -Path $CommandRoot | Out-Null
    Copy-Item -LiteralPath (Join-Path $ProjectRoot "integrations\cursor\imreview.md") `
        -Destination (Join-Path $CommandRoot "imreview.md") -Force
    $UpdatePrompt = Get-Content -Raw -LiteralPath (
        Join-Path $ProjectRoot "integrations\cursor\imupdate.md"
    )
    $UpdatePrompt = $UpdatePrompt.Replace(
        "{{INFERMATRIX_COPILOT_ROOT}}",
        $ProjectRoot
    )
    [IO.File]::WriteAllText(
        (Join-Path $CommandRoot "imupdate.md"),
        $UpdatePrompt,
        (New-Object Text.UTF8Encoding($false))
    )
}

if ($DryRun) {
    Write-Host "Would install InferMatrixCopilot for $Agent."
    Write-Host "Project: $ProjectRoot"
    Write-Host "Config root: $ConfigRoot"
    exit 0
}

Push-Location $ProjectRoot
try {
    $PythonExe = Find-CompatiblePython
    $Version = & $PythonExe -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
    Write-Host "Using Python $Version"

    & $PythonExe -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the Python virtual environment."
    }

    & $VenvPython -m pip install --disable-pip-version-check --no-input --quiet `
        "mcp>=1.2,<2" "PyYAML>=6.0"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install the MCP runtime."
    }

    switch ($Agent) {
        "codex" {
            if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
                throw "Codex CLI is not on PATH."
            }
            Remove-McpRegistration "codex" @("mcp", "remove", "infermatrix_copilot")
            & codex mcp add infermatrix_copilot --env "PYTHONPATH=$PythonPath" -- `
                $VenvPython -m infermatrix_copilot.thin_mcp_server
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to register InferMatrixCopilot with Codex."
            }
            Install-AgentSkills (Join-Path $ConfigRoot ".codex\skills")
            $InvokeText = "/imreview <PR URL>  or  /imupdate <repo path>"
        }
        "claude" {
            if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
                throw "Claude Code CLI is not on PATH."
            }
            Remove-McpRegistration "claude" @(
                "mcp", "remove", "--scope", "user", "infermatrix_copilot"
            )
            & claude mcp add --transport stdio --scope user `
                --env "PYTHONPATH=$PythonPath" infermatrix_copilot -- `
                $VenvPython -m infermatrix_copilot.thin_mcp_server
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to register InferMatrixCopilot with Claude Code."
            }
            Install-AgentSkills (Join-Path $ConfigRoot ".claude\skills")
            $InvokeText = "/imreview <PR URL>  or  /imupdate <repo path>"
        }
        "cursor" {
            Install-CursorConfig
            $InvokeText = "/imreview <PR URL>  or  /imupdate <repo path>"
        }
    }

    Write-Host ""
    Write-Host "Installed for $Agent. Restart it, then run:"
    Write-Host "  $InvokeText"
}
finally {
    Pop-Location
}
