$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $ProjectRoot
try {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -c "import sys; assert sys.version_info >= (3, 11), 'Python 3.11+ required'"
        if ($LASTEXITCODE -ne 0) {
            throw "The default Python 3 is older than 3.11."
        }
        & py -3 -m venv .venv
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -c "import sys; assert sys.version_info >= (3, 11), 'Python 3.11+ required'"
        if ($LASTEXITCODE -ne 0) {
            throw "Python 3.11+ is required."
        }
        & python -m venv .venv
    }
    else {
        throw "Python 3.11+ is required."
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the Python virtual environment."
    }

    $VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    $McpCommand = Join-Path $ProjectRoot ".venv\Scripts\infermatrix-copilot-mcp.exe"
    & $VenvPython -m pip install -e ".[mcp]"

    if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
        throw "Codex CLI is not on PATH."
    }
    & codex mcp add infermatrix_copilot -- $McpCommand

    Write-Host ""
    Write-Host "Installed. Restart Codex, then say:"
    Write-Host '  Use InferMatrixCopilot to review this PR: <PR URL>'
}
finally {
    Pop-Location
}
