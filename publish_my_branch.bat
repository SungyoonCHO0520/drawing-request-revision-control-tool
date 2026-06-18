@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ================================================
echo Publish current changes to your personal branch
echo ================================================
echo Project root: %CD%
echo.

where git >nul 2>nul
if errorlevel 1 (
    echo ERROR: git command was not found. Install Git or check PATH.
    pause
    exit /b 1
)

for /f "delims=" %%B in ('git branch --show-current') do set "BRANCH=%%B"
if not defined BRANCH (
    echo ERROR: Current Git branch could not be detected.
    pause
    exit /b 1
)

echo Current branch: %BRANCH%
if /i "%BRANCH%"=="main" (
    echo ERROR: Direct publishing from main is not allowed.
    echo Switch to sungyoon-codex or hakseok-claude and try again.
    pause
    exit /b 1
)

if /i not "%BRANCH%"=="sungyoon-codex" if /i not "%BRANCH%"=="hakseok-claude" (
    echo ERROR: This script only supports sungyoon-codex or hakseok-claude.
    pause
    exit /b 1
)

if exist ".\.venv\Scripts\python.exe" (
    set "PYTHON=.\.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

echo.
echo [1/7] Running full pytest...
"%PYTHON%" -m pytest
if errorlevel 1 (
    echo.
    echo ERROR: Tests failed. Commit and push were cancelled.
    pause
    exit /b 1
)

echo.
echo [2/7] Current git status:
git status --short

echo.
set "COMMIT_MSG="
set /p COMMIT_MSG=Enter commit message: 
if not defined COMMIT_MSG (
    echo ERROR: Commit message is required.
    pause
    exit /b 1
)

echo.
echo [3/7] Staging safe source code and tests only...
git reset --quiet
git add -- main.py requirements.txt README.md AGENTS.md CLAUDE.md desktop src tests *.bat

rem Never stage confidential documents, project databases, or local environments.
git reset --quiet -- .venv venv __pycache__ .pytest_cache 2>nul
git reset --quiet -- *.pdf *.PDF *.xlsx *.xls *.xlsm *.csv *.pfcproj *.db *.sqlite *.sqlite3 2>nul
git reset --quiet -- .env .env.* secrets credentials 2>nul

echo.
echo Files staged for commit:
git diff --cached --name-only

git diff --cached --quiet
if not errorlevel 1 (
    echo.
    echo Nothing safe to commit. Commit and push were cancelled.
    pause
    exit /b 0
)

echo.
echo [4/7] Creating commit on %BRANCH%...
git commit -m "%COMMIT_MSG%"
if errorlevel 1 (
    echo.
    echo ERROR: Commit failed. Push was cancelled.
    pause
    exit /b 1
)

echo.
echo [5/7] Pulling origin/%BRANCH% with rebase...
git pull --rebase origin "%BRANCH%"
if errorlevel 1 (
    echo.
    echo ERROR: Pull --rebase failed or conflicts occurred.
    echo Resolve the conflict, run tests again, and retry publishing.
    echo Push was cancelled.
    pause
    exit /b 1
)

echo.
echo [6/7] Pushing to origin/%BRANCH%...
git push -u origin "%BRANCH%"
if errorlevel 1 (
    echo.
    echo ERROR: Push failed.
    pause
    exit /b 1
)

echo.
echo [7/7] Publish completed successfully.
echo Branch: %BRANCH%
echo Latest Commit ID:
git rev-parse HEAD
echo.
pause

