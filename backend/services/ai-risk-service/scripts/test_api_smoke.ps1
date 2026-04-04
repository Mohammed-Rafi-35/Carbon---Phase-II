Param(
    [string]$BaseUrl = "http://localhost:8003",
    [string]$JwtSecret = "change-me-in-production"
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

$token = & $PythonExe -c "from datetime import datetime, timedelta, timezone; import jwt; print(jwt.encode({'sub':'smoke-test','role':'service','exp': datetime.now(tz=timezone.utc) + timedelta(hours=2)}, '$JwtSecret', algorithm='HS256'))"
$token = $token.Trim()

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

Write-Host "Testing AI Risk API at $BaseUrl"

$evaluatePayload = @{
    zone = "MR-2"
    metrics = @{
        disruption_freq = 0.30
        duration = 18
        traffic = 0.62
        order_drop = 0.20
        activity = 0.84
        claims = 0.15
    }
    context = @{
        rolling_disruption_3h = 0.25
        traffic_last_hour = 0.56
        previous_risk_score = 0.41
    }
} | ConvertTo-Json -Depth 6

$evaluateResponse = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/risk/evaluate" -Headers $headers -Body $evaluatePayload
Write-Host "Evaluate response:" ($evaluateResponse | ConvertTo-Json -Depth 6)

$healthResponse = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/v1/risk/health" -Headers $headers
Write-Host "Health response:" ($healthResponse | ConvertTo-Json -Depth 6)

$driftResponse = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/v1/risk/drift" -Headers $headers
Write-Host "Drift response:" ($driftResponse | ConvertTo-Json -Depth 6)

$predictionId = $evaluateResponse.data.prediction_id
$parsedPredictionId = 0
if ([int64]::TryParse("$predictionId", [ref]$parsedPredictionId) -and $parsedPredictionId -gt 0) {
    $feedbackPayload = @{
        prediction_id = $parsedPredictionId
        actual_outcome = 0.22
        corrected_label = "LOW"
        review_notes = "Smoke test feedback entry"
    } | ConvertTo-Json -Depth 6

    $feedbackResponse = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/risk/feedback" -Headers $headers -Body $feedbackPayload
    Write-Host "Feedback submit response:" ($feedbackResponse | ConvertTo-Json -Depth 6)
}

$listResponse = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/v1/risk/feedback?status=pending&limit=5" -Headers $headers
Write-Host "Feedback list response:" ($listResponse | ConvertTo-Json -Depth 6)

Write-Host "Smoke test completed."
