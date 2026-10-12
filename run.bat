@echo off
title EduPredict AI Launcher
echo ========================================================
echo        Starting EduPredict AI (Streamlit)
echo ========================================================
echo.
cd /d "%~dp0"

echo [1/2] Verifying Python installation...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b %errorlevel%
)

echo.
echo [2/2] Launching EduPredict AI on http://localhost:8501 ...
start "" "http://localhost:8501"
python -m streamlit run app.py
pause
