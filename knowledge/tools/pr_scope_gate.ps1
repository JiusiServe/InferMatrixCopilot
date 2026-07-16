param(
    [string]$RepoPath = ".",
    [string]$BaseRef = "origin/main",
    [string]$ScopeFile = "",
    [switch]$PrintTemplate
)

$ErrorActionPreference = "Stop"

function Write-Template {
    @"
# PR scope gate

Root owner:
- <file/function that owns the root cause>

Changed file mapping:
| File | Root owner or downstream symptom | Why current PR must touch it | Minimal alternative rejected |
| --- | --- | --- | --- |
| <path> | <owner/symptom> | <reason> | <why not smaller> |

Test mapping:
| Test file | Behavior protected | Source code change it binds to | Reviewer/comment/bug evidence |
| --- | --- | --- | --- |
| <path> | <behavior> | <path/function> | <anchor> |

Sub-agent finding triage:
| Finding | Root owner | Downstream affected | Action in this PR |
| --- | --- | --- | --- |
| <finding> | <owner> | <affected modules> | <patch owner only / no-op / follow-up> |

Out-of-scope deleted:
- <file/test/patch removed because it did not bind to current PR>

Cross-model reason:
- <required only when multiple model directories are touched>
"@
}

if ($PrintTemplate) {
    Write-Template
    exit 0
}

$repoRoot = (git -C $RepoPath rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    Write-Error "Cannot resolve git root for RepoPath=$RepoPath"
    exit 1
}

$changed = @(git -C $repoRoot diff --name-only "$BaseRef...HEAD" | Where-Object { $_ -ne "" })
if ($changed.Count -eq 0) {
    Write-Host "pr_scope_gate: no changed files from $BaseRef...HEAD"
    exit 0
}

Write-Host "pr_scope_gate: changed files from $BaseRef...HEAD"
foreach ($file in $changed) {
    Write-Host " - $file"
}

$risky = @()
foreach ($file in $changed) {
    if ($file -match '(^|/)tests/' -or
        $file -match '^examples/' -or
        $file -match '^vllm_omni/entrypoints/' -or
        $file -match '^vllm_omni/(model_executor|diffusion)/') {
        $risky += $file
    }
}

if ($risky.Count -eq 0) {
    Write-Host "pr_scope_gate: no risky code/test surface detected"
    exit 0
}

if (-not $ScopeFile) {
    $ScopeFile = Join-Path $repoRoot ".codex\pr_scope_gate.md"
}

if (-not (Test-Path -LiteralPath $ScopeFile)) {
    Write-Error "pr_scope_gate failed: missing scope ledger at $ScopeFile. Run with -PrintTemplate and fill it before push."
    exit 1
}

$scope = Get-Content -LiteralPath $ScopeFile -Raw -Encoding utf8
$requiredSections = @(
    "Root owner:",
    "Changed file mapping:",
    "Test mapping:",
    "Sub-agent finding triage:",
    "Out-of-scope deleted:"
)

foreach ($section in $requiredSections) {
    if (-not $scope.Contains($section)) {
        Write-Error "pr_scope_gate failed: scope ledger missing section '$section'"
        exit 1
    }
}

$missingFiles = @()
foreach ($file in $risky) {
    if (-not $scope.Contains($file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Error "pr_scope_gate failed: risky changed files missing from scope ledger:`n$($missingFiles -join "`n")"
    exit 1
}

$models = @()
foreach ($file in $changed) {
    if ($file -match '^vllm_omni/(?:model_executor/models|diffusion/models)/([^/]+)/') {
        $models += $Matches[1]
    }
}
$models = @($models | Sort-Object -Unique)

if ($models.Count -gt 1 -and -not $scope.Contains("Cross-model reason:")) {
    Write-Error "pr_scope_gate failed: multiple model directories touched ($($models -join ', ')); add Cross-model reason."
    exit 1
}

$testFiles = @($changed | Where-Object { $_ -match '(^|/)tests/' })
if ($testFiles.Count -gt 0 -and -not $scope.Contains("Behavior protected")) {
    Write-Error "pr_scope_gate failed: tests changed but Test mapping does not state protected behavior."
    exit 1
}

Write-Host "pr_scope_gate: passed"
