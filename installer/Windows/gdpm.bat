@echo off
setlocal enabledelayedexpansion

:: Check if VC++ Redistributable is installed
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" >nul 2>&1
if %errorlevel% equ 0 (
    echo VC++ Redistributable is installed.
    goto :run
)

echo.
echo ============================================
echo  Missing: Visual C++ Redistributable
echo ============================================
echo.
echo  gdpm requires the Microsoft Visual C++
echo  Redistributable to run on Windows.
echo.
echo  This is a one-time installation.
echo.

set /p INSTALL="Download and install now? (y/n): "
if /I not "%INSTALL%"=="y" (
    echo.
    echo You can download manually from:
    echo   https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo.
    pause
    exit /b 1
)

echo.
echo Downloading VC++ Redistributable...
curl -L -o "%TEMP%\vc_redist.x64.exe" "https://aka.ms/vs/17/release/vc_redist.x64.exe"
if %errorlevel% neq 0 (
    echo Failed to download. Please install manually.
    pause
    exit /b 1
)

echo Installing...
"%TEMP%\vc_redist.x64.exe" /install /quiet /norestart
if %errorlevel% neq 0 (
    echo Installation failed. Please install manually.
    pause
    exit /b 1
)

del "%TEMP%\vc_redist.x64.exe" 2>nul
echo.
echo Installed successfully!

:run
:: Run gdpm
"%~dp0_internal\gdpm.exe" %*
