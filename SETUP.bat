@echo off
setlocal
title Process Watchdog v3 - Setup
color 0A
echo.
echo  ================================================
echo   Process Watchdog v3 - First Time Setup
echo  ================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install Python 3.9+ and add to PATH.
    pause & exit /b 1
)

echo  [1/3] Installing packages...
python -m pip install --upgrade pip --quiet
python -m pip install -r "%~dp0requirements.txt" --quiet
if errorlevel 1 (
    echo  [ERROR] Dependency installation failed.
    pause & exit /b 1
)
echo        Done.
echo.

echo  [2/3] Registering startup...
python "%~dp0watchdog.py" --register-startup
if errorlevel 1 (
    echo  [WARN] Startup registration failed. You can retry from Settings later.
)
echo.

echo  [3/3] Launching Watchdog...
start "" pythonw "%~dp0watchdog.py"
echo        Running in system tray.
echo.

echo  ================================================
echo   Done!
echo.
echo   - A welcome screen will appear to pick your apps
echo   - WD icon lives in your system tray
echo   - Click it anytime to open the dashboard
echo   - Starts automatically with Windows
echo  ================================================
echo.
pause
