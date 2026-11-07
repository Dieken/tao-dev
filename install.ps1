# Project-only skill deployment; no client configuration or dependency preparation.
param(
    [Parameter(Mandatory=$true)][ValidateSet('claude','codex','cursor','kiro')][string]$Client,
    [Parameter(Mandatory=$true)][string]$Project,
    [string]$Source
)
$ErrorActionPreference = 'Stop'
$python = $null
$prefix = @()
foreach ($candidate in @('python3','python','py')) {
    if (!(Get-Command $candidate -ErrorAction SilentlyContinue)) { continue }
    $candidatePrefix = if ($candidate -eq 'py') { @('-3') } else { @() }
    & $candidate @candidatePrefix -c 'import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,15) else 1)'
    if ($LASTEXITCODE -eq 0) { $python = $candidate; $prefix = $candidatePrefix; break }
}
if (!$python) { throw 'Python 3.11–3.14 is required; installation needs no pip or document packages.' }
$work = $null
try {
    $entry = if ($PSScriptRoot) { Join-Path $PSScriptRoot 'skills/tao-dev/scripts/tao.py' } else { $null }
    if (!$entry -or !(Test-Path -LiteralPath $entry -PathType Leaf)) {
        $null = Get-Command git -ErrorAction Stop
        $work = Join-Path ([IO.Path]::GetTempPath()) ('tao-install-' + [guid]::NewGuid().ToString('N'))
        git clone --quiet --depth 1 https://github.com/Dieken/tao-dev.git (Join-Path $work 'source')
        if ($LASTEXITCODE -ne 0) { throw 'Could not download tao-dev.' }
        $entry = Join-Path $work 'source/skills/tao-dev/scripts/tao.py'
    }
    $arguments = @('install','--client',$Client,'--project',$Project)
    if ($Source) { $arguments += @('--source',$Source) }
    & $python @prefix -I -B $entry @arguments
    if ($LASTEXITCODE -ne 0) { throw 'tao install did not complete; inspect its report.' }
} finally {
    if ($work -and (Test-Path -LiteralPath $work)) { Remove-Item -LiteralPath $work -Recurse -Force }
}
