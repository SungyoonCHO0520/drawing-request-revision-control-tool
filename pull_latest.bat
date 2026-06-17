@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ================================================
echo Pull latest GitHub main and verify local project
echo ================================================
echo Project root: %CD%
echo.

where git >nul 2>nul
if errorlevel 1 (
    echo ERROR: git command was not found. Install Git or check PATH.
    pause
    exit /b 1
)

echo [1/5] Pulling latest main...
git pull origin main
if errorlevel 1 (
    echo.
    echo ERROR: git pull failed. Resolve the error above before continuing.
    pause
    exit /b 1
)

if not exist ".\.venv\Scripts\python.exe" (
    echo.
    echo [2/5] Creating local virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create .venv.
        pause
        exit /b 1
    )
)

set "PYTHON=.\.venv\Scripts\python.exe"

echo.
echo [3/5] Installing requirements...
"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: pip install failed.
    pause
    exit /b 1
)

echo.
echo [4/5] Running full pytest...
"%PYTHON%" -m pytest
if errorlevel 1 (
    echo.
    echo ERROR: Tests failed after pulling latest main.
    pause
    exit /b 1
)

echo.
echo [5/5] Latest Commit ID:
git rev-parse HEAD

echo.
echo Pull and verification completed successfully.
pause
