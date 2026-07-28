@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "PROJECT=C:\Users\user\Desktop\drawing-request-revision-control-tool-main"
set "GIT=%PROJECT%\.runtime\PortableGit\cmd\git.exe"
if not exist "%GIT%" set "GIT=git"
if not exist "%PROJECT%\.git" (
  echo ERROR: Git repository was not found.
  pause
  exit /b 1
)
"%GIT%" -c "safe.directory=C:/Users/user/Desktop/drawing-request-revision-control-tool-main" -C "%PROJECT%" config --local user.name "Sungyoon Cho"
if errorlevel 1 goto fail
"%GIT%" -c "safe.directory=C:/Users/user/Desktop/drawing-request-revision-control-tool-main" -C "%PROJECT%" config --local user.email "syjo@changsung.com"
if errorlevel 1 goto fail
echo.
echo Team Sync Git identity configured successfully.
echo Name: Sungyoon Cho
echo Email: syjo@changsung.com
echo.
echo Return to Team Sync and click My Work Upload again.
pause
exit /b 0
:fail
echo.
echo ERROR: Failed to configure the repository Git identity.
pause
exit /b 1
