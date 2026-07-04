<#
.SYNOPSIS
    ccs - list / search Claude Code sessions (wrapper around ccsessions.py).
.DESCRIPTION
    Finds a Python interpreter, then runs ccsessions.py (next to this script)
    with UTF-8 output, forwarding all arguments.

    Examples:
      ccs                       # sessions from the last 2h
      ccs --since 30m           # custom window
      ccs --all                 # no time filter
      ccs --grep "threat"       # search message content
      ccs --project acl         # filter by project path
      ccs --pick                # interactive picker -> resume
      ccs --show <uuid>         # dump one transcript
#>
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'

$script = Join-Path $PSScriptRoot 'ccsessions.py'
if (-not (Test-Path $script)) {
    Write-Error "ccsessions.py not found next to ccs.ps1 ($script)"
    exit 1
}

# Resolve a Python interpreter: prefer the launcher, then python/python3,
# then the known Program Files install.
$py = $null
foreach ($cand in @('py', 'python', 'python3')) {
    $cmd = Get-Command $cand -ErrorAction SilentlyContinue
    if ($cmd) { $py = $cmd.Source; break }
}
if (-not $py) {
    $fallback = 'C:\Program Files\Python313\python.exe'
    if (Test-Path $fallback) { $py = $fallback }
}
if (-not $py) {
    Write-Error 'No Python interpreter found (tried py, python, python3).'
    exit 1
}

& $py $script @Args
exit $LASTEXITCODE
