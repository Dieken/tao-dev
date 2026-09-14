# Native PowerShell counterpart; Python owns preparation and execution policy.
param([ValidateSet('cli', 'hook', 'validate')][string]$Target = 'cli',
      [Parameter(ValueFromRemainingArguments = $true)][string[]]$TaoArguments)
$ErrorActionPreference = 'Stop'
if ($Target -eq 'hook') {
    $project = (Get-Location).Path
    while (!(Test-Path (Join-Path $project '.tao/config.toml'))) {
        $parent = Split-Path $project -Parent
        if (!$parent -or $parent -eq $project) { Write-Output '{}'; exit 0 }
        $project = $parent
    }
}
$entry = @{cli='tao.py'; hook='hook.py'; validate='validate_documents.py'}[$Target]
$probe = 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 2)'
$candidates = if ($env:TAO_PYTHON) { @($env:TAO_PYTHON) } else { @('python3', 'python', 'py') }
foreach ($candidate in $candidates) {
    $prefix = if (!$env:TAO_PYTHON -and $candidate -eq 'py') { @('-3') } else { @() }
    try {
        $null = Get-Command $candidate -ErrorAction Stop
        & $candidate @prefix -I -c $probe 2>$null
        if ($LASTEXITCODE -eq 0) {
            & $candidate @prefix -I -B (Join-Path $PSScriptRoot $entry) @TaoArguments
            exit $LASTEXITCODE
        }
    } catch { continue }
}
if ($Target -eq 'hook') {
    Write-Output '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"tao docs not_run: Python 3.11+ is unavailable; configure TAO_PYTHON."}}'
    exit 0
}
Write-Output '{"tool":"tao-dev","status":"not_run","diagnostics":[{"rule_id":"TAO-RUNTIME-001","message":"Python 3.11+ is unavailable; configure TAO_PYTHON."}]}'
exit 2
