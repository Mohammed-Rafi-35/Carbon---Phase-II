Param(
    [switch]$SkipTrain,
    [switch]$OpenNotebook
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

Set-Location $ServiceRoot

Write-Host "Using Python: $PythonExe"
Write-Host "Service root: $ServiceRoot"

Write-Host "Step 1/5: Generate synthetic data"
& $PythonExe -m ml.src.data_generation

Write-Host "Step 2/5: Build HITL feedback dataset"
& $PythonExe -m ml.src.build_feedback_dataset

if (-not $SkipTrain) {
    Write-Host "Step 3/5: Train model"
    & $PythonExe -m ml.src.train
} else {
    Write-Host "Step 3/5: Skipped training"
}

Write-Host "Step 4/5: Evaluate model"
& $PythonExe -m ml.src.evaluate

Write-Host "Step 5/5: Generate visualization report"
& $PythonExe -m ml.src.generate_visuals

if ($OpenNotebook) {
    $notebookPath = Join-Path $ServiceRoot "ml\notebooks\model_evaluation.ipynb"
    Write-Host "Opening notebook: $notebookPath"
    jupyter notebook $notebookPath
}

Write-Host "Done. Check ml/models/metadata.json, ml/models/evaluation_report.json, and ml/models/reports/."
