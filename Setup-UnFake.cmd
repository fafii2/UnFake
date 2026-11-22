@echo off
cd /d "%~dp0"
echo Preparing UnFake. Please keep this window open until setup finishes.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup-UnFake.ps1"
if errorlevel 1 (
  echo.
  echo Setup failed. Read the error above before closing this window.
) else (
  echo.
  echo Setup finished. You can now open Start-UnFake.cmd.
)
pause
