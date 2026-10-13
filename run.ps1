# EduPredict AI Node.js Launcher
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       Launching EduPredict AI (Node.js)                " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

node --version
if ($LASTEXITCODE -ne 0) {
    Write-Error "Node.js 18 or newer is required."
    exit 1
}

Write-Host "Starting web server on http://localhost:8501..." -ForegroundColor Green
Start-Process "http://localhost:8501"
node server.js
