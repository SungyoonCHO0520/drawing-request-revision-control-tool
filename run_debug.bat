@echo off
cd /d "C:\Users\User\Documents\Codex\2026-05-18\files-mentioned-by-the-user-20260205\pfc_in_drawing_request_tool"

set QT_QPA_PLATFORM=

echo Starting Drawing Request & Revision Control Tool...
echo Current path:
cd

echo.
echo Checking python...
.\.venv\Scripts\python.exe --version

echo.
echo Running app...
.\.venv\Scripts\python.exe desktop\app.py

echo.
echo If the app did not open, check the error message above.
pause