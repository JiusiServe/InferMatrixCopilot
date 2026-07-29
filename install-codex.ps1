$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $ProjectRoot
try {
    $PythonCandidates = @()

    if (Get-Command py -ErrorAction SilentlyContinue) {
        $PreviousErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $LauncherOutput = & py -0p 2>$null
        $ErrorActionPreference = $PreviousErrorActionPreference
        $LauncherOutput | ForEach-Object {
            if ($_ -match '^\s*-\S+\s+\*?\s*(.+?)\s*$') {
                $PythonCandidates += $Matches[1].Trim().Trim('"')
            }
        }
    }

    foreach ($Name in @("python", "python3")) {
        $Resolved = Get-Command $Name -ErrorAction SilentlyContinue
        if ($Resolved) {
            $PythonCandidates += $Resolved.Source
        }
    }

    $PythonExe = $null
    foreach ($Candidate in $PythonCandidates | Select-Object -Unique) {
        if (-not (Test-Path -LiteralPath $Candidate) -and
            -not (Get-Command $Candidate -ErrorAction SilentlyContinue)) {
            continue
        }
        & $Candidate -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $PythonExe = $Candidate
            break
        }
    }

    if (-not $PythonExe) {
        throw "No compatible Python found. Install any Python 3.11 or newer."
    }

    $PythonVersion = & $PythonExe -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
    Write-Host "Using Python $PythonVersion at $PythonExe"
    & $PythonExe -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the Python virtual environment."
    }

    $VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    & $VenvPython -m pip install --disable-pip-version-check --no-input "mcp>=1.2,<2"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install the MCP runtime."
    }

    if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
        throw "Codex CLI is not on PATH."
    }
    $PythonPath = Join-Path $ProjectRoot "src"
    & codex mcp add infermatrix_copilot --env "PYTHONPATH=$PythonPath" -- `
        $VenvPython -m infermatrix_copilot.thin_mcp_server
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to register infermatrix_copilot with Codex."
    }

    Write-Host ""
    Write-Host "Installed. Restart Codex, then say:"
    Write-Host '  Use InferMatrixCopilot to review this PR: <PR URL>'
}
finally {
    Pop-Location
}
