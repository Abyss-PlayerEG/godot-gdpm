@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "INSTALL_DIR=%LOCALAPPDATA%\gdpm"
set "LANG_CHOICE=%GDPM_INSTALL_LANG%"
set "ASSUME_YES="

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--lang" (
    set "LANG_CHOICE=%~2"
    shift
    shift
    goto parse_args
)
if /I "%~1"=="-y" (
    set "ASSUME_YES=1"
    shift
    goto parse_args
)
if /I "%~1"=="--yes" (
    set "ASSUME_YES=1"
    shift
    goto parse_args
)
if /I "%~1"=="-h" goto usage
if /I "%~1"=="--help" goto usage
echo Unknown option: %~1
goto usage_error

:args_done
if /I "!LANG_CHOICE!"=="zh" set "LANG_CHOICE=zh"
if /I "!LANG_CHOICE!"=="zh-cn" set "LANG_CHOICE=zh"
if /I "!LANG_CHOICE!"=="cn" set "LANG_CHOICE=zh"
if /I "!LANG_CHOICE!"=="en" set "LANG_CHOICE=en"
if /I "!LANG_CHOICE!"=="en-us" set "LANG_CHOICE=en"
if defined LANG_CHOICE if not "!LANG_CHOICE!"=="zh" if not "!LANG_CHOICE!"=="en" (
    echo Unsupported language "!LANG_CHOICE!", falling back to English.
    echo 不支持的语言 "!LANG_CHOICE!", 已回退到英文.
    set "LANG_CHOICE=en"
)

if not defined LANG_CHOICE (
    if defined ASSUME_YES (
        set "LANG_CHOICE=en"
    ) else (
        echo ============================================
        echo   Select language / 选择语言
        echo ============================================
        echo   [1] English - default
        echo   [2] 中文
        echo.
        set /p "LANG_PICK=  > "
        if not defined LANG_PICK set "LANG_PICK=1"
        if "!LANG_PICK!"=="2" (
            set "LANG_CHOICE=zh"
        ) else (
            set "LANG_CHOICE=en"
        )
    )
)

if /I "!LANG_CHOICE!"=="zh" (
    set "T_TITLE=gdpm 卸载程序 - Windows"
    set "T_CONFIRM=确认卸载 gdpm? (y/n): "
    set "T_CANCELLED=已取消."
    set "T_REMOVED=✓ 已移除 %INSTALL_DIR%"
    set "T_NOT_FOUND=未在 %INSTALL_DIR% 找到 gdpm"
    set "T_PATH_REMOVED=✓ 已从 PATH 中移除"
    set "T_PATH_ABSENT=PATH 中无此项"
    set "T_DONE=卸载完成. 配置目录 ~/.gdpm 已保留."
    set "T_DELETE_HINT=如需彻底清理, 请手动删除: rmdir /S /Q %USERPROFILE%\.gdpm"
) else (
    set "T_TITLE=gdpm Uninstaller - Windows"
    set "T_CONFIRM=Remove gdpm? (y/n): "
    set "T_CANCELLED=Cancelled."
    set "T_REMOVED=✓ Removed %INSTALL_DIR%"
    set "T_NOT_FOUND=gdpm not found in %INSTALL_DIR%"
    set "T_PATH_REMOVED=✓ Removed from PATH"
    set "T_PATH_ABSENT=Not present in PATH"
    set "T_DONE=Done. Config at ~/.gdpm was preserved."
    set "T_DELETE_HINT=Delete manually if needed: rmdir /S /Q %USERPROFILE%\.gdpm"
)

echo ============================================
echo  !T_TITLE!
echo ============================================
echo.

if not defined ASSUME_YES (
    set /p "CONFIRM=  !T_CONFIRM!"
    if not defined CONFIRM set "CONFIRM=n"
    if /I not "!CONFIRM!"=="y" if /I not "!CONFIRM!"=="yes" if not "!CONFIRM!"=="是" if not "!CONFIRM!"=="确认" (
        echo   !T_CANCELLED!
        goto finish
    )
)

if exist "%INSTALL_DIR%\gdpm.exe" (
    rmdir /S /Q "%INSTALL_DIR%"
    echo   !T_REMOVED!
) else (
    echo   !T_NOT_FOUND!
)

set "CUR_PATH="
for /f "skip=2 tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "CUR_PATH=%%B"
if defined CUR_PATH (
    set "NEW_PATH=!CUR_PATH!"
    set "NEW_PATH=!NEW_PATH:;%INSTALL_DIR%=!"
    set "NEW_PATH=!NEW_PATH:%INSTALL_DIR%;=!"
    set "NEW_PATH=!NEW_PATH:%INSTALL_DIR%=!"
    if "!NEW_PATH!"=="!CUR_PATH!" (
        echo   !T_PATH_ABSENT!
    ) else (
        reg add "HKCU\Environment" /v Path /t REG_EXPAND_SZ /d "!NEW_PATH!" /f >nul
        echo   !T_PATH_REMOVED!
    )
) else (
    echo   !T_PATH_ABSENT!
)

echo.
echo   !T_DONE!
echo   !T_DELETE_HINT!
goto finish

:usage
echo Usage:   uninstall.bat [--lang en^|zh] [-y^|--yes]
echo 用法:    uninstall.bat [--lang en^|zh] [-y^|--yes]
exit /b 0

:usage_error
echo Usage:   uninstall.bat [--lang en^|zh] [-y^|--yes]
echo 用法:    uninstall.bat [--lang en^|zh] [-y^|--yes]
exit /b 1

:finish
if not defined ASSUME_YES pause
exit /b 0
