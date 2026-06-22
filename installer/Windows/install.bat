@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "INSTALL_DIR=%LOCALAPPDATA%\gdpm"
set "SRC=%~dp0"

echo ============================================
echo  gdpm Installer (Windows)
echo ============================================
echo.

if not exist "%SRC%gdpm.exe" (
    echo [ERROR] gdpm.exe not found
    pause
    exit /b 1
)

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo [1/3] Installing files...
copy /Y "%SRC%gdpm.exe" "%INSTALL_DIR%\" >nul
if exist "%SRC%install.bat" copy /Y "%SRC%install.bat" "%INSTALL_DIR%\" >nul 2>nul
if exist "%SRC%uninstall.bat" copy /Y "%SRC%uninstall.bat" "%INSTALL_DIR%\" >nul 2>nul
echo    Done.

echo [2/3] Configuring PATH...
for /f "skip=2 tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "CUR_PATH=%%B"

echo !CUR_PATH! | findstr /I /C:"%INSTALL_DIR%" >nul
if errorlevel 1 (
    if defined CUR_PATH (
        reg add "HKCU\Environment" /v Path /t REG_EXPAND_SZ /d "!CUR_PATH!;%INSTALL_DIR%" /f >nul
    ) else (
        reg add "HKCU\Environment" /v Path /t REG_EXPAND_SZ /d "%INSTALL_DIR%" /f >nul
    )
    echo    Added to PATH
) else (
    echo    Already in PATH
)

echo [3/3] Creating config directory...
if not exist "%USERPROFILE%\.config\gdpm" (
    mkdir "%USERPROFILE%\.config\gdpm"
    echo    Created
) else (
    echo    Already exists
)

echo.
echo ============================================
echo  Installation complete!
echo  Restart your terminal, then run:
echo    gdpm --help
echo ============================================
pause
