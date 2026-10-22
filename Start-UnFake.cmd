@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run Setup-UnFake.ps1 first.
  pause
  exit /b 1
)
echo UnFake is starting. Keep this window open while using the extension.
echo Demo: http://localhost:8000/demo
cd backend
"..\.venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
