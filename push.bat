@echo off
title Push EduPredict AI to GitHub
echo ========================================================
echo        Pushing EduPredict AI (CampusIQ) to GitHub
echo ========================================================
echo.
cd /d "%~dp0"

echo Repository: https://github.com/9963664914/CampusIQ-AI.git
echo Branch:     main
echo.
echo Pushing commit...
git push origin main

echo.
if %errorlevel% equ 0 (
    echo [SUCCESS] Code successfully pushed to GitHub!
) else (
    echo [NOTICE] If prompted by GitHub, please sign in through the browser window.
)
echo.
pause
