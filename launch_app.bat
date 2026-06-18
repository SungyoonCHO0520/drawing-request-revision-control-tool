@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call launch_and_sync.bat
exit /b %errorlevel%
