@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  goto setup
)
".venv\Scripts\python.exe" -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 goto setup
goto run

:setup
echo UnFake needs first-time setup or an environment repair.
echo Installing the required Python packages. Please keep this window open.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup-UnFake.ps1"
if errorlevel 1 goto setup_failed
".venv\Scripts\python.exe" -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 goto setup_failed

:run
echo UnFake is starting. Keep this window open while using the extension.
echo Open Facebook or a news page, then use the UnFake extension.
echo Backend status: http://127.0.0.1:8001/api/v1/health
cd backend
"..\.venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8001
pause
exit /b

:setup_failed
echo.
echo Setup could not finish. Read the error above before closing this window.
echo Project folder: %~dp0
pause
exit /b 1
