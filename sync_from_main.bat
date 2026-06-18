@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if exist ".\.venv\Scripts\python.exe" (
    set "PYTHON=.\.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

"%PYTHON%" tools\team_sync_cli.py sync-main --test
if errorlevel 1 (
    echo.
    echo ERROR: Main synchronization was stopped. Review the message above.
    pause
    exit /b 1
)
echo.
echo Current branch:
git branch --show-current
echo Latest Commit ID:
git rev-parse HEAD
pause

