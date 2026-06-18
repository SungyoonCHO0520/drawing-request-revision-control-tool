@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if exist ".\.venv\Scripts\python.exe" (
    set "PYTHON=.\.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

"%PYTHON%" tools\team_sync_cli.py integrate
if errorlevel 1 (
    echo.
    echo ERROR: Main integration was stopped. Review the message above.
    pause
    exit /b 1
)
echo.
echo Main integration completed successfully.
pause

