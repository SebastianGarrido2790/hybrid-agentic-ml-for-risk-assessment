@echo off
setlocal
title ACRAS - Agentic Credit Risk Assessment System

:: Clean screen and display banner
cls
echo ============================================================
echo   🚀 ACRAS: AGENTIC CREDIT RISK ASSESSMENT SYSTEM
echo ============================================================
echo.
echo [SYSTEM] Initializing Antigravity Stack...
echo.

:: Step 1: Check/Sync Dependencies
echo [1/3] Verifying dependencies with UV...
uv sync --quiet
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 🚨 Error: Failed to sync dependencies. Verify 'uv' is installed.
    pause
    exit /b %ERRORLEVEL%
)
echo      Done.
echo.

:: Step 2: Launch FastAPI in a separate minimized window
echo [2/3] Launching Risk Prediction API (FastAPI)...
echo      Endpoint: http://localhost:8000
:: Start the API window minimized to keep it tidy but accessible
start "ACRAS-API" /min cmd /k "title ACRAS-API && uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait for API to warm up
echo.
echo [WAIT] Stalling for API initialization (5s)...
timeout /t 5 >nul

:: Step 3: Launch Streamlit in the foreground
echo.
echo [3/3] Launching Intelligence Dashboard (Streamlit)...
echo      URL: http://localhost:8501
echo.
echo ------------------------------------------------------------
echo 💡 TIP: The API is running in the background (minimized).
echo    To stop EVERYTHING:
echo    1. Close the "ACRAS-API" window in the taskbar.
echo    2. Press Ctrl+C in this window.
echo ------------------------------------------------------------
echo.

:: Run Streamlit
uv run streamlit run src/ui/app.py

:: If the user stops Streamlit, give them a chance to read the exit message
echo.
echo [SYSTEM] ACRAS Sessions Terminated.
pause
