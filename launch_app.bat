@echo off
cd /d "C:\Users\User\Documents\Codex\2026-05-18\files-mentioned-by-the-user-20260205\pfc_in_drawing_request_tool"
set QT_QPA_PLATFORM=

if exist ".\.venv\Scripts\pythonw.exe" (
    start "" ".\.venv\Scripts\pythonw.exe" "desktop\app.py"
) else (
    start "" ".\.venv\Scripts\python.exe" "desktop\app.py"
)