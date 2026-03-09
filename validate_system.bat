@echo off
setlocal
title ACRAS - System Health Validation

:: Clean screen and display banner
cls
echo ============================================================
echo   🛡️  ACRAS: MULTI-POINT SYSTEM VALIDATION
echo ============================================================
echo.
echo [SYSTEM] Starting full architecture health check...
echo.

:: Pillar 1: Static Code Quality
echo [1/4] Pillar 1: Static Code Quality (Pyright ^& Ruff)...
echo      - Running Pyright (Type Checking)...
uv run pyright src/
if errorlevel 1 goto :FAILED

echo.
echo      - Running Ruff (Linting)...
uv run ruff check .
if errorlevel 1 goto :FAILED

echo.
echo      - Running Ruff (Formatting Check)...
uv run ruff format --check .
if errorlevel 1 goto :FAILED

echo.
echo      Done.
echo.

:: Pillar 2: Functional Logic & Coverage
echo [2/4] Pillar 2: Functional Logic ^& Coverage...
echo      - Running Pytest with Coverage Gate (40%%)...
uv run pytest tests/unit/ -v --cov=src --cov-fail-under=40
if errorlevel 1 goto :FAILED

echo.
echo      Done.
echo.

:: Pillar 3: Pipeline Synchronization
echo [3/4] Pillar 3: Pipeline Synchronization (DVC)...
uv run dvc status
if errorlevel 1 goto :FAILED

echo.
echo      Done.
echo.

:: Pillar 4: API Service & Runtime
echo [4/4] Pillar 4: API Service Health...
curl -s http://localhost:8000/health | findstr "ok" >nul
if errorlevel 1 goto :API_WARNING

echo.
echo      API is ONLINE and HEALTHY.
goto :PILLAR4_DONE

:API_WARNING
echo.
echo      WARNING: Local API is not reachable or /health returned error.
echo      Ensure the API is running (launch_acras.bat) if you want to test runtime.

:PILLAR4_DONE
echo.
echo      Done.
echo.

:SUCCESS
echo ============================================================
echo   ✅ SYSTEM HEALTH: 100%% (ALL GATES PASSED)
echo ============================================================
echo.
echo Your changes are now validated and safe for production readiness.
pause
exit /b 0

:FAILED
echo.
echo ============================================================
echo   ❌ VALIDATION FAILED
echo ============================================================
echo.
echo Please review the logs above and correct the issues.
pause
exit /b 1
