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
    echo Please run this script from the release directory.
    pause
    exit /b 1
)

:: Check VC++ Redistributable
echo [1/4] Checking dependencies...
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [WARNING] Visual C++ Redistributable not found.
    echo  gdpm requires it to run on Windows.
    echo.
    set /p INSTALL_VC="  Download and install now? (y/n): "
    if /I "!INSTALL_VC!"=="y" (
        echo.
        echo  Downloading VC++ Redistributable...
        curl -L -o "%TEMP%\vc_redist.x64.exe" "https://aka.ms/vs/17/release/vc_redist.x64.exe"
        if !errorlevel! equ 0 (
            echo  Installing...
            "%TEMP%\vc_redist.x64.exe" /install /quiet /norestart
            del "%TEMP%\vc_redist.x64.exe" 2>nul
            echo  Done.
        ) else (
            echo  [ERROR] Download failed. Please install manually.
            echo  https://aka.ms/vs/17/release/vc_redist.x64.exe
        )
    ) else (
        echo.
        echo  Please install manually before running gdpm:
        echo  https://aka.ms/vs/17/release/vc_redist.x64.exe
    )
    echo.
) else (
    echo    VC++ Redistributable: OK
)

echo [2/4] Installing files...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

if exist "%INSTALL_DIR%\_internal" rmdir /S /Q "%INSTALL_DIR%\_internal"
copy /Y "%SRC%gdpm.exe" "%INSTALL_DIR%\" >nul
if exist "%SRC%_internal\" (
    xcopy /E /Y /I /Q "%SRC%_internal" "%INSTALL_DIR%\_internal\" >nul
)
if exist "%SRC%install.bat" copy /Y "%SRC%install.bat" "%INSTALL_DIR%\" >nul 2>nul
if exist "%SRC%uninstall.bat" copy /Y "%SRC%uninstall.bat" "%INSTALL_DIR%\" >nul 2>nul
echo    Done.

echo [3/4] Configuring PATH...
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

echo [4/4] Creating config directory...
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
