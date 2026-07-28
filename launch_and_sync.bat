@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if defined PFC_PYTHON (
    if exist "%PFC_PYTHON%" (
        set "PYTHON=%PFC_PYTHON%"
        goto run_sync
    )
)
if exist ".\.venv\Scripts\python.exe" (
    set "PYTHON=.\.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

:run_sync
"%PYTHON%" tools\team_sync_cli.py launch-sync --launch
if errorlevel 1 (
    echo.
    echo ERROR: Safe startup synchronization failed. The app was not started.
    pause
    exit /b 1
)
exit /b 0
