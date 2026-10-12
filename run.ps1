# EduPredict AI PowerShell Launcher
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       Launching EduPredict AI (Streamlit)              " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

Write-Host "Starting web server on http://localhost:8501..." -ForegroundColor Green
Start-Process "http://localhost:8501"
python -m streamlit run app.py
