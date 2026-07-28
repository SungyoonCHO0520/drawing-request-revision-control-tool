@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "APP_NAME=DrawingRequestRevisionTool"
set "BUILD_VENV=%LOCALAPPDATA%\DrawingRequestRevisionTool\build-venv"
set "BUILD_PY=%BUILD_VENV%\Scripts\python.exe"
set "CODEX_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "OUTPUT_DIR=%CD%\release"
set "WORK_DIR=%TEMP%\DrawingRequestRevisionTool\pyinstaller-build"
set "SPEC_DIR=%TEMP%\DrawingRequestRevisionTool\pyinstaller-spec"

if exist "%BUILD_PY%" goto install

where py.exe >nul 2>nul
if not errorlevel 1 (
    set "BASE_PY=py.exe"
    set "BASE_ARGS=-3"
    goto create_venv
)

where python.exe >nul 2>nul
if not errorlevel 1 (
    set "BASE_PY=python.exe"
    set "BASE_ARGS="
    goto create_venv
)

if exist "%CODEX_PY%" (
    set "BASE_PY=%CODEX_PY%"
    set "BASE_ARGS="
    goto create_venv
)

echo.
echo ERROR: Python 3 was not found.
echo Install Python 3 on this build PC and run build_standalone.bat again.
pause
exit /b 1

:create_venv
echo.
echo Creating the EXE build environment...
"%BASE_PY%" %BASE_ARGS% -m venv "%BUILD_VENV%"
if errorlevel 1 goto fail

:install
echo.
echo Installing build packages...
"%BUILD_PY%" -m pip install --upgrade pip
if errorlevel 1 goto fail
"%BUILD_PY%" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto fail

echo.
echo Building the standalone Windows EXE...
"%BUILD_PY%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name "%APP_NAME%" ^
    --hidden-import fitz ^
    --exclude-module pytest ^
    --exclude-module pygments ^
    --paths "%CD%" ^
    --distpath "%OUTPUT_DIR%" ^
    --workpath "%WORK_DIR%" ^
    --specpath "%SPEC_DIR%" ^
    desktop\app.py
if errorlevel 1 goto fail

echo.
echo Build completed:
echo %OUTPUT_DIR%\%APP_NAME%.exe
explorer "%OUTPUT_DIR%"
exit /b 0

:fail
echo.
echo ERROR: Standalone EXE build failed.
pause
exit /b 1
