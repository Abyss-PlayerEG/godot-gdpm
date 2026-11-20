@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

rem ===== 卸载: 只撤销用户 PATH 条目 (HKCU) —— 无需管理员, 不删除任何文件 =====
set "LEGACY_DIR=%LOCALAPPDATA%\gdpm"
set "MARKER=%LOCALAPPDATA%\gdpm-install.txt"
set "TARGET_DIR=%~dp0"
if "%TARGET_DIR:~-1%"=="\" set "TARGET_DIR=%TARGET_DIR:~0,-1%"
set "LANG_CHOICE=%GDPM_INSTALL_LANG%"
set "ASSUME_YES="

rem 优先读安装时记录的位置 (目录被移动过也能正确清理旧 PATH 条目; 旧版 marker 的 scope 行会被忽略)
if exist "%MARKER%" (
    for /f "usebackq delims=" %%A in ("%MARKER%") do (
        for /f "tokens=1,* delims==" %%B in ("%%A") do (
            if /I "%%B"=="dir" if not "%%C"=="" set "TARGET_DIR=%%C"
        )
    )
)
set "LEGACY="
if exist "%LEGACY_DIR%\gdpm.exe" set "LEGACY=1"

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
    rem 显示语言默认跟随 Windows 显示语言, zh 开头即中文
    set "SYS_LOCALE="
    for /f "skip=2 tokens=3" %%A in ('reg query "HKCU\Control Panel\International" /v LocaleName 2^>nul') do set "SYS_LOCALE=%%A"
    if /I "!SYS_LOCALE:~0,2!"=="zh" (set "LANG_CHOICE=zh") else (set "LANG_CHOICE=en")
)

if /I "!LANG_CHOICE!"=="zh" (
    set "T_TITLE=gdpm 卸载程序 - Windows"
    set "T_PLAN=本脚本将执行以下操作:"
    set "T_ITEM1=- 从用户 PATH 中移除: !TARGET_DIR!"
    set "T_ITEM2=- 清理旧版安装副本 %LOCALAPPDATA%\gdpm"
    set "T_ITEM3=- 不删除任何文件 (解压目录原样保留)"
    set "T_ITEM4=- 保留配置目录 ~/.gdpm"
    set "T_WHY_HEAD=为什么只清 PATH:"
    set "T_WHY1=  与 Linux/macOS 一致: 安装只写了用户 PATH (全程无需管理员),"
    set "T_WHY2=  卸载只撤销这一条 —— 你的程序文件与配置不会被删除."
    set "T_CONFIRM=确认卸载 gdpm? (y/n): "
    set "T_CANCELLED=已取消."
    set "T_REMOVED=✓ 已从用户 PATH 中移除 !TARGET_DIR!"
    set "T_PATH_ABSENT=⚠ 用户 PATH 中未找到 !TARGET_DIR!"
    set "T_PATH_GUARD=⛔ 安全拦截: 移除结果异常, 已放弃写入 (PATH 原样保留)"
    set "T_SYS_RESIDUAL=⚠ 系统 PATH 中仍有本目录 (旧版系统级安装残留): 请以管理员身份手动移除该条目."
    set "T_LEGACY_FOUND=检测到旧版安装副本, 正在清理 (含其 PATH 条目)..."
    set "T_LEGACY_DONE=✓ 旧版安装已清理"
    set "T_LEGACY_NONE=未发现旧版安装副本"
    set "T_MARKER_DONE=✓ 已移除安装记录"
    set "T_DONE=卸载完成. 程序文件与配置目录 ~/.gdpm 均已保留."
    set "T_DELETE_HINT=如需彻底清理, 另请手动删除你的解压目录, 以及配置: rmdir /S /Q %USERPROFILE%\.gdpm"
) else (
    set "T_TITLE=gdpm Uninstaller - Windows"
    set "T_PLAN=This script will:"
    set "T_ITEM1=- Remove from user PATH: !TARGET_DIR!"
    set "T_ITEM2=- Clean up legacy install copy at %LOCALAPPDATA%\gdpm"
    set "T_ITEM3=- Delete no files (your extracted folder is kept)"
    set "T_ITEM4=- Keep the config directory at ~/.gdpm"
    set "T_WHY_HEAD=Why PATH-only cleanup:"
    set "T_WHY1=  Same as Linux/macOS: install wrote only the user PATH (no admin),"
    set "T_WHY2=  uninstalling only reverts it — your files and config stay untouched."
    set "T_CONFIRM=Remove gdpm? (y/n): "
    set "T_CANCELLED=Cancelled."
    set "T_REMOVED=✓ Removed from user PATH: !TARGET_DIR!"
    set "T_PATH_ABSENT=⚠ Not found in user PATH: !TARGET_DIR!"
    set "T_PATH_GUARD=⛔ Safety guard: removal result invalid; PATH left unchanged"
    set "T_SYS_RESIDUAL=⚠ This folder is still in the SYSTEM PATH (legacy system-scope install): remove it manually with an elevated session."
    set "T_LEGACY_FOUND=Legacy install copy found, cleaning (including its PATH entry)..."
    set "T_LEGACY_DONE=✓ Legacy install cleaned"
    set "T_LEGACY_NONE=No legacy install copy found"
    set "T_MARKER_DONE=✓ Install record removed"
    set "T_DONE=Done. Program files and config at ~/.gdpm were preserved."
    set "T_DELETE_HINT=For a full cleanup also delete your extracted folder and run: rmdir /S /Q %USERPROFILE%\.gdpm"
)

echo ============================================
echo  !T_TITLE!
echo ============================================
echo.
echo   !T_PLAN!
echo   !T_ITEM1!
if defined LEGACY echo   !T_ITEM2!
echo   !T_ITEM3!
echo   !T_ITEM4!
echo.
echo   !T_WHY_HEAD!
echo   !T_WHY1!
echo   !T_WHY2!
echo.

if not defined ASSUME_YES (
    echo   !T_CONFIRM!
    set /p "CONFIRM=> "
    if not defined CONFIRM set "CONFIRM=n"
    if /I not "!CONFIRM!"=="y" if /I not "!CONFIRM!"=="yes" if not "!CONFIRM!"=="是" if not "!CONFIRM!"=="确认" (
        echo   !T_CANCELLED!
        goto finish
    )
)
echo.

rem ===== 从用户 PATH 移除目标条目 (HKCU 当前用户可写, 永不触发 UAC) =====
rem 注意: 替换模式里必须用 %TARGET_DIR% (解析时先展开),
rem 用 !TARGET_DIR! 嵌套延迟展开是非法语法, 曾把 PATH 写坏
set "CUR_PATH="
for /f "skip=2 tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "CUR_PATH=%%B"
set "NEW_PATH="
if defined CUR_PATH (
    set "NEW_PATH=!CUR_PATH!"
    set "NEW_PATH=!NEW_PATH:;%TARGET_DIR%=!"
    set "NEW_PATH=!NEW_PATH:%TARGET_DIR%;=!"
    set "NEW_PATH=!NEW_PATH:%TARGET_DIR%=!"
    if "!NEW_PATH!"=="!CUR_PATH!" (
        echo !T_PATH_ABSENT!
    ) else (
        set "GUARD_OK=1"
        echo !NEW_PATH! | findstr /I /C:"%TARGET_DIR%" >nul
        if not errorlevel 1 set "GUARD_OK="
        if defined GUARD_OK (
            reg add "HKCU\Environment" /v Path /t REG_EXPAND_SZ /d "!NEW_PATH!" /f >nul
            echo !T_REMOVED!
        ) else (
            echo !T_PATH_GUARD!
        )
    )
) else (
    echo !T_PATH_ABSENT!
)

if exist "%MARKER%" (
    del "%MARKER%" >nul 2>&1
    echo !T_MARKER_DONE!
)

rem ===== 旧系统级安装残留检测 (只读查询, 无需权限) =====
set "SYS_RESIDUAL="
for /f "skip=2 tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_RESIDUAL=%%B"
if defined SYS_RESIDUAL (
    echo !SYS_RESIDUAL! | findstr /I /C:"%TARGET_DIR%" >nul
    if not errorlevel 1 echo !T_SYS_RESIDUAL!
)

rem ===== 旧版复制安装清理 (仅旧版存在的副本与它的 HKCU PATH 条目) =====
if defined LEGACY (
    echo !T_LEGACY_FOUND!
    set "OLD_PATH="
    for /f "skip=2 tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "OLD_PATH=%%B"
    if defined OLD_PATH (
        set "CLEANED=!OLD_PATH!"
        set "CLEANED=!CLEANED:;%LEGACY_DIR%=!"
        set "CLEANED=!CLEANED:%LEGACY_DIR%;=!"
        set "CLEANED=!CLEANED:%LEGACY_DIR%=!"
        reg add "HKCU\Environment" /v Path /t REG_EXPAND_SZ /d "!CLEANED!" /f >nul
    )
    rmdir /S /Q "%LEGACY_DIR%" >nul 2>&1
    echo !T_LEGACY_DONE!
) else (
    echo !T_LEGACY_NONE!
)

rem ===== 广播环境变量变更, 让新开终端立即可见 =====
set "GDPM_PS=%TEMP%\gdpm_broadcast.ps1"
>"!GDPM_PS!" echo Add-Type -Name GdpmEnv -Namespace Win32 -MemberDefinition '[DllImport("user32.dll", SetLastError=true, CharSet=CharSet.Auto)] public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);'
>>"!GDPM_PS!" echo $r = [UIntPtr]::Zero
>>"!GDPM_PS!" echo [Win32.GdpmEnv]::SendMessageTimeout([IntPtr]0xffff, 0x1A, [UIntPtr]::Zero, "Environment", 2, 5000, [ref]$r) ^| Out-Null
powershell -NoProfile -ExecutionPolicy Bypass -File "!GDPM_PS!" >nul 2>&1
del "!GDPM_PS!" >nul 2>&1

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
