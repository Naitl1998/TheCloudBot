Write-Host ""
Write-Host "=== Render Setup ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Open render.com -> Account Settings -> API Keys"
Write-Host "2. Click [+ Create API Key], name it 'bot'"
Write-Host "3. Copy the key and paste below"
Write-Host ""
$API_KEY = Read-Host "Paste Render API key"
if (-not $API_KEY) { Write-Host "No key provided. Exit." -ForegroundColor Red; exit 1 }
$BOT_TOKEN = "8780268115:AAEeOZ1vAjTd2BiLaAA_IS_Pz2cuPnkuMGM"
$WEBHOOK_DOMAIN = "https://the-cloud-booking.onrender.com"
$HEADERS = @{ Authorization = "Bearer $API_KEY"; "Content-Type" = "application/json" }
Write-Host "Searching for service on Render..." -ForegroundColor Yellow
try {
    $services = Invoke-RestMethod -Uri "https://api.render.com/v1/services?limit=50" -Headers $HEADERS -ErrorAction Stop
} catch {
    Write-Host "ERROR: Bad API key or network problem." -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}
$service = $services | Where-Object { $_.service.serviceDetails.url -like "*the-cloud-booking*" } | Select-Object -First 1
if (-not $service) {
    $service = $services | Where-Object { $_.service.name -like "*cloud*" -or $_.service.name -like "*booking*" } | Select-Object -First 1
}
if ($service) {
    $SERVICE_ID = $service.service.id
    $SERVICE_NAME = $service.service.name
    Write-Host "OK Found service: $SERVICE_NAME (ID: $SERVICE_ID)" -ForegroundColor Green
} else {
    Write-Host "No service found. Creating new one..." -ForegroundColor Yellow
    $body = '{"type":"web_service","name":"the-cloud-booking","repo":"https://github.com/Naitl1998/TheCloudBot","branch":"master","buildCommand":"pip install -r requirements.txt","startCommand":"python bot.py","plan":"free","region":"oregon","runtime":"python"}'
    $new = Invoke-RestMethod -Uri "https://api.render.com/v1/services" -Method POST -Headers $HEADERS -Body $body
    $SERVICE_ID = $new.service.id
    Write-Host "OK Service created (ID: $SERVICE_ID)" -ForegroundColor Green
}
Write-Host "Setting environment variables..." -ForegroundColor Yellow
$envJson = '[{"key":"BOT_TOKEN","value":"' + $BOT_TOKEN + '"},{"key":"WEBHOOK_DOMAIN","value":"' + $WEBHOOK_DOMAIN + '"}]'
Invoke-RestMethod -Uri "https://api.render.com/v1/services/$SERVICE_ID/env-vars" -Method PUT -Headers $HEADERS -Body $envJson | Out-Null
Write-Host "OK Env vars set" -ForegroundColor Green
Write-Host "Triggering deploy..." -ForegroundColor Yellow
Invoke-RestMethod -Uri "https://api.render.com/v1/services/$SERVICE_ID/deploys" -Method POST -Headers $HEADERS -Body "{}" | Out-Null
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  DONE! Bot is deploying on Render." -ForegroundColor Green
Write-Host "  Ready in ~2-3 minutes." -ForegroundColor Green
Write-Host "  URL: $WEBHOOK_DOMAIN" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green