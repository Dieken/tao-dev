# Download the installer and delegate installation policy to tao install.
param(
    [ValidateSet('claude','codex','cursor')][string]$Client = 'codex',
    [ValidateSet('user','project','repo','local')][string]$Scope = 'user',
    [string]$Project = (Get-Location).Path,
    [string]$Source,
    [string]$Marketplace,
    [string]$Wheelhouse
)
$ErrorActionPreference = 'Stop'
if ($Source -and $Marketplace) { throw 'Source and Marketplace are mutually exclusive.' }
$python = $null
$prefix = @()
foreach ($candidate in @('python3','python','py')) {
    if (!(Get-Command $candidate -ErrorAction SilentlyContinue)) { continue }
    $candidatePrefix = if ($candidate -eq 'py') { @('-3') } else { @() }
    & $candidate @candidatePrefix -c 'import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,15) else 1)'
    if ($LASTEXITCODE -eq 0) { $python = $candidate; $prefix = $candidatePrefix; break }
}
if (!$python) { throw 'Python 3.11–3.14 with pip, venv and ensurepip is required.' }
$null = Get-Command git -ErrorAction Stop
$work = Join-Path ([IO.Path]::GetTempPath()) ('tao-install-' + [guid]::NewGuid().ToString('N'))
try {
    git clone --quiet --depth 1 https://github.com/Dieken/tao-dev.git (Join-Path $work 'source')
    if ($LASTEXITCODE -ne 0) { throw 'Could not download tao-dev.' }
    $arguments = @('install','--client',$Client,'--scope',$Scope,'--project',$Project)
    if ($Source) { $arguments += @('--source',$Source) }
    if ($Marketplace) { $arguments += @('--marketplace',$Marketplace) }
    if ($Wheelhouse) { $arguments += @('--wheelhouse',$Wheelhouse) }
    $entry = Join-Path $work 'source/plugins/tao-dev/skills/tao-dev/scripts/tao.py'
    & $python @prefix -I -B $entry @arguments
    if ($LASTEXITCODE -ne 0) { throw 'tao install did not complete; inspect its report.' }
} finally {
    if (Test-Path $work) { Remove-Item -LiteralPath $work -Recurse -Force }
}
