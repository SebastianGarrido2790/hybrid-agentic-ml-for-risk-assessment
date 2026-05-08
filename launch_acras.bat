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

:: Step 0: Check for Observability (Optional)
echo [0/4] Checking for Observability Stack (Jaeger)...
echo      UI: http://localhost:16686
echo      Note: Run 'docker run --rm -d -p 16686:16686 -p 4318:4318 jaegertracing/all-in-one:latest' 
echo            to enable full distributed tracing.
echo.

:: Step 1: Check/Sync Dependencies
echo [1/4] Verifying dependencies with UV...
uv sync --quiet
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 🚨 Error: Failed to sync dependencies. Verify 'uv' is installed.
    pause
    exit /b %ERRORLEVEL%
)
echo      Done.
echo.

:: Step 2: Launch MLflow Tracking Server
echo [2/4] Launching MLflow Tracking Server...
echo      UI: http://127.0.0.1:5000
start "ACRAS-MLflow" /min cmd /k "title ACRAS-MLflow && launch_mlflow.bat"

:: Step 3: Launch FastAPI in a separate minimized window
echo [3/4] Launching Risk Prediction API (FastAPI)...
echo      Endpoint: http://localhost:8000
:: Start the API window minimized to keep it tidy but accessible
start "ACRAS-API" /min cmd /k "title ACRAS-API && uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait for services to warm up
echo.
echo [WAIT] Stalling for service initialization (5s)...
timeout /t 5 >nul

:: Step 4: Launch Streamlit in the foreground
echo.
echo [4/4] Launching Intelligence Dashboard (Streamlit)...
echo      URL: http://localhost:8501
echo.
echo ------------------------------------------------------------
echo 💡 TIP: The API and MLflow are running in the background.
echo    To stop EVERYTHING:
echo    1. Close the "ACRAS-API" window.
echo    2. Close the "ACRAS-MLflow" window.
echo    3. Press Ctrl+C in this window.
echo.
echo 🔍 OBSERVABILITY: If you started Jaeger via Docker,
echo    visit http://localhost:16686 to see live traces.
echo ------------------------------------------------------------
echo.

:: Run Streamlit
uv run streamlit run src/ui/app.py

:: If the user stops Streamlit, give them a chance to read the exit message
echo.
echo [SYSTEM] ACRAS Sessions Terminated.
pause
