$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptRoot "tunnel_remote_fuseagent.py"

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $pythonCommand) {
    throw "Python is required to run the fuseAgent SSH tunnel script."
}

if ($pythonCommand.Name -eq "py.exe" -or $pythonCommand.Name -eq "py") {
    & $pythonCommand.Source -3 $pythonScript
} else {
    & $pythonCommand.Source $pythonScript
}
