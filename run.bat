@echo off
title EduPredict AI Launcher
echo ========================================================
echo        Starting EduPredict AI (Node.js)
echo ========================================================
echo.
cd /d "%~dp0"

echo [1/2] Verifying Node.js installation...
node --version
if %errorlevel% neq 0 (
    echo [ERROR] Node.js 18 or newer is required.
    pause
    exit /b 1
)

echo.
echo [2/2] Launching EduPredict AI on http://localhost:8501 ...
start "" "http://localhost:8501"
node server.js
pause
