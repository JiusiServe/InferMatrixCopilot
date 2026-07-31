[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("codex", "claude", "cursor")]
    [string]$Agent,

    [string]$ConfigRoot = [Environment]::GetFolderPath("UserProfile"),

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Installer = Join-Path $ProjectRoot "scripts\install_mcp.py"

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

$PythonExe = Find-CompatiblePython
$InstallerArgs = @(
    $Installer,
    $Agent,
    "--config-root",
    $ConfigRoot
)
if ($DryRun) {
    $InstallerArgs += "--dry-run"
}

& $PythonExe @InstallerArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
