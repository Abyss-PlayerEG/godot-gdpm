@echo off
setlocal enabledelayedexpansion

set "INSTALL_DIR=%LOCALAPPDATA%\gdpm"

echo ============================================
echo  gdpm Uninstaller (Windows)
echo ============================================
echo.

set /p CONFIRM="Remove gdpm? (y/n): "
if /I not "%CONFIRM%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

if exist "%INSTALL_DIR%\gdpm.exe" (
    rmdir /S /Q "%INSTALL_DIR%"
    echo Removed %INSTALL_DIR%
) else (
    echo gdpm not found in %INSTALL_DIR%
)

echo.
echo Done. Config at %USERPROFILE%\.config\gdpm was preserved.
pause
