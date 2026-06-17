@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ================================================
echo Publish current source changes to GitHub main
echo ================================================
echo Project root: %CD%
echo.

where git >nul 2>nul
if errorlevel 1 (
    echo ERROR: git command was not found. Install Git or check PATH.
    pause
    exit /b 1
)

if exist ".\.venv\Scripts\python.exe" (
    set "PYTHON=.\.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

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
if "%COMMIT_MSG%"=="" (
    echo ERROR: Commit message is required.
    pause
    exit /b 1
)

echo.
echo [3/7] Resetting staged files and staging safe project files only...
git reset --quiet

git add -- main.py README.md AGENTS.md CLAUDE.md publish_to_github.bat pull_latest.bat desktop src tests

rem Never stage confidential data, generated reports, project DB files, or local runtime files.
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
echo [4/7] Creating commit...
git commit -m "%COMMIT_MSG%"
if errorlevel 1 (
    echo.
    echo ERROR: Commit failed. Push was cancelled.
    pause
    exit /b 1
)

echo.
echo [5/7] Pulling latest main with rebase...
git pull --rebase origin main
if errorlevel 1 (
    echo.
    echo ERROR: Pull --rebase failed or conflicts occurred.
    echo Resolve conflicts manually, run tests again, then push after confirming.
    echo Push was cancelled.
    pause
    exit /b 1
)

echo.
echo [6/7] Pushing to origin main...
git push origin main
if errorlevel 1 (
    echo.
    echo ERROR: Push failed.
    pause
    exit /b 1
)

echo.
echo [7/7] Latest Commit ID:
git rev-parse HEAD

echo.
echo Publish completed successfully.
pause
