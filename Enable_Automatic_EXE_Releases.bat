@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "PROJECT=C:\Users\user\Desktop\drawing-request-revision-control-tool-main"
set "SOURCE=%~dp0build-windows-exe.yml"
set "TARGET=%PROJECT%\.github\workflows\build-windows-exe.yml"

if not exist "%PROJECT%\.git" (
  echo ERROR: Project Git repository was not found.
  echo %PROJECT%
  pause
  exit /b 1
)

if not exist "%SOURCE%" (
  echo ERROR: Workflow template was not found.
  echo %SOURCE%
  pause
  exit /b 1
)

if not exist "%PROJECT%\.github\workflows" (
  mkdir "%PROJECT%\.github\workflows"
  if errorlevel 1 goto fail
)

copy /Y "%SOURCE%" "%TARGET%" >nul
if errorlevel 1 goto fail

echo.
echo Automatic EXE release workflow was installed successfully.
echo.
echo Next:
echo 1. Open Team Sync.
echo 2. Click "My Work Upload".
echo 3. Use commit message: Automate EXE releases
echo.
echo GitHub will test, build, and publish the next EXE release automatically.
pause
exit /b 0

:fail
echo.
echo ERROR: Failed to install the automatic EXE release workflow.
pause
exit /b 1
