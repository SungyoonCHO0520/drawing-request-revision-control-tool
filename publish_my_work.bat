@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if exist ".\.venv\Scripts\python.exe" (
    set "PYTHON=.\.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

"%PYTHON%" tools\team_sync_cli.py publish
if errorlevel 1 (
    echo.
    echo ERROR: Upload was stopped. Review the message above.
    pause
    exit /b 1
)
echo.
echo Upload completed successfully.
pause

