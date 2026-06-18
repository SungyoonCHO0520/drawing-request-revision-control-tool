@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if exist ".\.venv\Scripts\python.exe" (
    set "PYTHON=.\.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

"%PYTHON%" tools\team_sync_cli.py launch-sync --launch
if errorlevel 1 (
    echo.
    echo ERROR: Safe startup synchronization failed. The app was not started.
    pause
    exit /b 1
)
exit /b 0

