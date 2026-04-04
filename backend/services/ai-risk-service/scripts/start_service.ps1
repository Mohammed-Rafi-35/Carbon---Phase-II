Param(
    [int]$Port = 8003
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServiceRoot = Resolve-Path (Join-Path $ScriptDir "..")
$ProjectRoot = Resolve-Path (Join-Path $ServiceRoot "..\..\..")

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
} else {
    $PythonExe = "python"
}

Write-Host "Starting AI Risk Service"
Write-Host "Service root: $ServiceRoot"
Write-Host "Python executable: $PythonExe"
Write-Host "Port: $Port"

Set-Location $ServiceRoot
& $PythonExe -m uvicorn app.main:app --host 0.0.0.0 --port $Port
