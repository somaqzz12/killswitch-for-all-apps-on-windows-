@echo off
setlocal
title Process Watchdog - Build EXE
color 0A
echo.
echo  ================================================
echo   Process Watchdog - Build to EXE
echo  ================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    pause & exit /b 1
)

echo  [1/3] Installing build dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r "%~dp0requirements-build.txt" --quiet
if errorlevel 1 (
    echo  [ERROR] Build dependencies install failed.
    pause & exit /b 1
)
echo        Done.
echo.

echo  [2/3] Building EXE with PyInstaller...
python -m PyInstaller watchdog.spec --clean --noconfirm
echo.

if not exist "dist\ProcessWatchdog.exe" (
    echo  [ERROR] Build failed. Check output above for errors.
    echo  [TIP] If you see "Access is denied", exit ProcessWatchdog.exe from the tray and try again.
    pause & exit /b 1
)

echo  [3/3] Done!
echo.
echo  ================================================
echo   Output: dist\ProcessWatchdog.exe
echo.
echo   Share just that one file.
echo   No Python needed on the target machine.
echo  ================================================
echo.

:: Open the dist folder
explorer dist

pause
