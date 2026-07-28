@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PORTABLE_GIT_CMD=%CD%\.runtime\PortableGit\cmd"
if exist "%PORTABLE_GIT_CMD%\git.exe" set "PATH=%PORTABLE_GIT_CMD%;%PATH%"
set "GIT_CONFIG_COUNT=1"
set "GIT_CONFIG_KEY_0=safe.directory"
set "GIT_CONFIG_VALUE_0=%CD:\=/%"

set "LOCAL_VENV_DIR=%CD%\.venv"
set "USER_VENV_DIR=%LOCALAPPDATA%\DrawingRequestRevisionTool\.venv"
set "TEMP_VENV_DIR=%TEMP%\DrawingRequestRevisionTool\.venv"
set "CODEX_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "VENV_DIR=%LOCAL_VENV_DIR%"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "REQ_FILE=%CD%\requirements.txt"
set "SETUP_MARKER=%VENV_DIR%\.pfc_setup_complete"

call :ensure_python
if errorlevel 1 goto fail

call :ensure_venv
if errorlevel 1 goto fail

call :ensure_requirements
if errorlevel 1 goto fail

if /I "%~1"=="--setup-only" exit /b 0

if exist "%CD%\.git" (
    set "PFC_PYTHON=%VENV_PY%"
    call "%~dp0launch_and_sync.bat"
    exit /b %errorlevel%
)

echo.
echo Git metadata was not found. Starting in standalone mode without Team Sync.
set "PFC_STANDALONE=1"
"%VENV_PY%" desktop\app.py
exit /b %errorlevel%

:ensure_python
if exist "%VENV_PY%" exit /b 0
if exist "%USER_VENV_DIR%\Scripts\python.exe" (
    call :use_venv "%USER_VENV_DIR%"
    exit /b 0
)
if exist "%TEMP_VENV_DIR%\Scripts\python.exe" (
    call :use_venv "%TEMP_VENV_DIR%"
    exit /b 0
)
where py.exe >nul 2>nul
if not errorlevel 1 (
    set "BASE_PY=py -3"
    call :use_venv "%USER_VENV_DIR%"
    exit /b 0
)
where python.exe >nul 2>nul
if not errorlevel 1 (
    set "BASE_PY=python"
    call :use_venv "%USER_VENV_DIR%"
    exit /b 0
)
if exist "%CODEX_PY%" (
    set "BASE_PY=%CODEX_PY%"
    call :use_venv "%USER_VENV_DIR%"
    exit /b 0
)
echo.
echo ERROR: Python 3 was not found.
echo Install Python 3 first, then run this file again.
echo Download: https://www.python.org/downloads/
pause
exit /b 1

:use_venv
set "VENV_DIR=%~1"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "SETUP_MARKER=%VENV_DIR%\.pfc_setup_complete"
exit /b 0

:ensure_venv
if exist "%VENV_PY%" exit /b 0
echo.
echo First run setup: creating the local Python environment...
%BASE_PY% -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo.
    echo ERROR: Failed to create .venv.
    exit /b 1
)
if not exist "%VENV_PY%" (
    echo.
    echo ERROR: .venv was created, but python.exe was not found.
    exit /b 1
)
exit /b 0

:ensure_requirements
if not exist "%REQ_FILE%" exit /b 0
if exist "%SETUP_MARKER%" exit /b 0
echo.
echo First run setup: installing required packages...
"%VENV_PY%" -m pip --version >nul 2>nul
if errorlevel 1 (
    "%VENV_PY%" -m ensurepip --upgrade
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to prepare pip.
        exit /b 1
    )
)
"%VENV_PY%" -m pip install -r "%REQ_FILE%"
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install required packages.
    echo Check your network connection, then run this file again.
    exit /b 1
)
type nul > "%SETUP_MARKER%"
exit /b 0

:fail
echo.
echo Startup stopped. Please fix the error above and run launch_app.bat again.
pause
exit /b 1
