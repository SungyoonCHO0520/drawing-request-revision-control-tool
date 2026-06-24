@echo off
setlocal EnableExtensions
cd /d "%~dp0"

call :switch_branch hakseok-claude
if errorlevel 1 goto :switch_failed

echo.
echo Branch switch successful: hakseok-claude
echo Current branch:
git branch --show-current

set "HAS_LOCAL_CHANGES="
for /f "delims=" %%S in ('git status --porcelain') do set "HAS_LOCAL_CHANGES=1"
if defined HAS_LOCAL_CHANGES goto :skip_pull

echo Pulling latest origin/hakseok-claude...
git pull --rebase origin hakseok-claude
if errorlevel 1 goto :pull_failed
echo Pull completed successfully.
goto :launch

:skip_pull
echo Local changes detected. Skipping pull to protect your work.
goto :launch

:pull_failed
echo WARNING: Branch switch succeeded, but pull failed.
echo Starting the program with the current local branch state.
goto :launch

:launch
echo Starting PFC IN Drawing Request Tool...
if exist ".\.venv\Scripts\python.exe" (
    ".\.venv\Scripts\python.exe" tools\team_sync_cli.py profile --branch hakseok-claude
) else (
    python tools\team_sync_cli.py profile --branch hakseok-claude
)
call "%~dp0launch_app.bat"
exit /b 0

:switch_branch
set "TARGET_BRANCH=%~1"
where git >nul 2>nul
if errorlevel 1 exit /b 1

git show-ref --verify --quiet "refs/heads/%TARGET_BRANCH%"
if errorlevel 1 (
    git fetch origin "%TARGET_BRANCH%"
    if errorlevel 1 exit /b 1
    git switch --track -c "%TARGET_BRANCH%" "origin/%TARGET_BRANCH%"
) else (
    git switch "%TARGET_BRANCH%"
)
exit /b %errorlevel%

:switch_failed
echo.
echo ERROR: Could not switch to hakseok-claude.
echo The program was not started. Check the Git branch and local changes.
pause
exit /b 1
