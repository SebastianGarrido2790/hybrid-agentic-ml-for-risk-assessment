@echo off
setlocal
title ACRAS - MLflow Tracking Server

echo ============================================================
echo   📊 MLFLOW TRACKING SERVER (ACRAS)
echo ============================================================
echo.
echo [SYSTEM] Launching MLflow with Production-Ready Local Config...
echo.
echo      Backend: sqlite:///mlflow_system.db
echo      Artifacts: ./artifacts/mlflow_storage
echo      Host: 127.0.0.1
echo      Port: 5000
echo.
echo ------------------------------------------------------------
echo 💡 TIP: Keep this window open while running pipelines.
echo    Access UI at: http://127.0.0.1:5000
echo ------------------------------------------------------------
echo.

:: Run the MLflow server
uv run python -m mlflow server ^
    --backend-store-uri sqlite:///mlflow_system.db ^
    --default-artifact-root ./artifacts/mlflow_storage ^
    --host 127.0.0.1 ^
    --port 5000

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 🚨 Error: MLflow server failed to start.
    pause
)
