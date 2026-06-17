@echo off
setlocal EnableExtensions
cd /d "%~dp0"

call :switch_and_update hakseok-claude
if errorlevel 1 goto :failed

echo.
echo Current branch:
git branch --show-current
echo Starting PFC IN Drawing Request Tool...
call :launch_app
exit /b 0

:switch_and_update
set "TARGET_BRANCH=%~1"
where git >nul 2>nul
if errorlevel 1 exit /b 1

git fetch origin
if errorlevel 1 exit /b 1

git show-ref --verify --quiet "refs/heads/%TARGET_BRANCH%"
if errorlevel 1 (
    git switch --track -c "%TARGET_BRANCH%" "origin/%TARGET_BRANCH%"
) else (
    git switch "%TARGET_BRANCH%"
)
if errorlevel 1 exit /b 1

git pull --rebase origin "%TARGET_BRANCH%"
exit /b %errorlevel%

:launch_app
set QT_QPA_PLATFORM=
if exist ".\.venv\Scripts\pythonw.exe" (
    start "" ".\.venv\Scripts\pythonw.exe" "desktop\app.py"
) else if exist ".\.venv\Scripts\python.exe" (
    start "" ".\.venv\Scripts\python.exe" "desktop\app.py"
) else (
    start "" pythonw "desktop\app.py"
)
exit /b 0

:failed
echo.
echo ERROR: Could not switch to or update hakseok-claude.
echo Check network access and resolve any local Git conflicts first.
pause
exit /b 1
