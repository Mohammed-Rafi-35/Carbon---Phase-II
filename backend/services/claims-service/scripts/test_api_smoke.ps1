Param(
    [string]$BaseUrl = "http://localhost:8013",
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

$serviceToken = & $PythonExe -c "from datetime import datetime, timedelta, timezone; import jwt; print(jwt.encode({'sub':'8beea6d7-c470-45ff-b0a0-4e025fdb0f2f','role':'service','exp': datetime.now(tz=timezone.utc) + timedelta(hours=2)}, '$JwtSecret', algorithm='HS256'))"
$workerToken = & $PythonExe -c "from datetime import datetime, timedelta, timezone; import jwt; print(jwt.encode({'sub':'16fd2706-8baf-433b-82eb-8c7fada847da','role':'worker','exp': datetime.now(tz=timezone.utc) + timedelta(hours=2)}, '$JwtSecret', algorithm='HS256'))"

$serviceHeaders = @{
    "Authorization" = "Bearer $($serviceToken.Trim())"
    "X-Request-ID" = "req-claims-smoke-001"
    "Content-Type" = "application/json"
}

$workerHeaders = @{
    "Authorization" = "Bearer $($workerToken.Trim())"
    "X-Request-ID" = "req-claims-smoke-002"
    "Content-Type" = "application/json"
}

Write-Host "[1/5] Health check"
$health = Invoke-RestMethod -Method Get -Uri "$BaseUrl/health"
Write-Host ($health | ConvertTo-Json -Depth 4)

Write-Host "[2/5] Auto create claim"
$createPayload = @{
    user_id = "16fd2706-8baf-433b-82eb-8c7fada847da"
    event_id = "99999999-9999-9999-9999-999999999999"
} | ConvertTo-Json -Depth 4
$created = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/claims/auto" -Headers $serviceHeaders -Body $createPayload
Write-Host ($created | ConvertTo-Json -Depth 6)

$claimId = $created.data.claim_id

Write-Host "[3/5] Process claim"
$processPayload = @{ claim_id = "$claimId" } | ConvertTo-Json -Depth 3
$processed = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/claims/process" -Headers $serviceHeaders -Body $processPayload
Write-Host ($processed | ConvertTo-Json -Depth 6)

Write-Host "[4/5] Fetch user claims"
$userClaims = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/v1/claims/16fd2706-8baf-433b-82eb-8c7fada847da" -Headers $workerHeaders
Write-Host ($userClaims | ConvertTo-Json -Depth 6)

Write-Host "[5/5] Fetch claim detail"
$detail = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/v1/claims/detail/$claimId" -Headers $serviceHeaders
Write-Host ($detail | ConvertTo-Json -Depth 8)

Write-Host "Smoke test completed for claims and decision engine."
