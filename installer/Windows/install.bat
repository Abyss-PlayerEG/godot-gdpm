@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

rem ===== 原地安装: 不复制文件, 只写用户 PATH (HKCU) —— 全程无需管理员 =====
set "SOURCE_DIR=%~dp0"
if "%SOURCE_DIR:~-1%"=="\" set "SOURCE_DIR=%SOURCE_DIR:~0,-1%"
set "LEGACY_DIR=%LOCALAPPDATA%\gdpm"
set "MARKER=%LOCALAPPDATA%\gdpm-install.txt"
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

rem ===== 语言默认值: 跟随 Windows 显示语言, 显式 --lang / GDPM_INSTALL_LANG 优先 =====
rem 系统语言是中文或英文(明确) → 直接采用不询问; 其他语言(gdpm 仅支持中英)才询问
set "DEFAULT_LANG=en"
set "LOCALE_SURE="
set "SYS_LOCALE="
for /f "skip=2 tokens=3" %%A in ('reg query "HKCU\Control Panel\International" /v LocaleName 2^>nul') do set "SYS_LOCALE=%%A"
if /I "!SYS_LOCALE:~0,2!"=="zh" (
    set "DEFAULT_LANG=zh"
    set "LOCALE_SURE=1"
)
if /I "!SYS_LOCALE:~0,2!"=="en" (
    set "DEFAULT_LANG=en"
    set "LOCALE_SURE=1"
)

rem ===== 语言选择 (未指定 --lang 且非 -y 时交互询问) =====
rem ===== 语言选择: 系统语言明确(中/英)时直接采用并告知, 不再询问; 其他语言才出菜单 =====
if not defined LANG_CHOICE (
    if defined ASSUME_YES (
        set "LANG_CHOICE=!DEFAULT_LANG!"
    ) else if defined LOCALE_SURE (
        set "LANG_CHOICE=!DEFAULT_LANG!"
        echo   Language: !LANG_CHOICE! - from Windows display language / 跟随 Windows 显示语言
    ) else (
        set "MARK_EN= - default"
        set "MARK_ZH="
        if "!DEFAULT_LANG!"=="zh" (
            set "MARK_EN="
            set "MARK_ZH= - 默认"
        )
        echo ============================================
        echo   Select language / 选择语言
        echo ============================================
        echo   [1] English!MARK_EN!
        echo   [2] 中文!MARK_ZH!
        echo.
        set /p "LANG_PICK=  > "
        if not defined LANG_PICK (
            if "!DEFAULT_LANG!"=="zh" (set "LANG_PICK=2") else (set "LANG_PICK=1")
        )
        if "!LANG_PICK!"=="2" (
            set "LANG_CHOICE=zh"
        ) else (
            set "LANG_CHOICE=en"
        )
    )
)

if /I "!LANG_CHOICE!"=="zh" (
    set "T_TITLE=gdpm 安装程序 - Windows"
    set "T_PLAN=本脚本将执行以下操作:"
    set "T_ITEM1=- 将本目录加入用户 PATH: %SOURCE_DIR% (不复制文件, 无需管理员)"
    set "T_ITEM2=- 创建配置目录 ~/.gdpm"
    set "T_WHY_HEAD=为什么这样安装:"
    set "T_WHY1=  与 Linux/macOS 一致: gdpm 在解压目录原地运行, PATH 指向这里,"
    set "T_WHY2=  不产生第二份拷贝. 请勿删除或移动本目录."
    set "T_WARRANTY=继续即表示你知晓: 本软件按现状提供, 不附带任何担保."
    set "T_CONFIRM=是否继续? (y/n): "
    set "T_CANCELLED=已取消安装."
    set "T_ERR_EXE=错误: 未找到 gdpm.exe, 请在解压后的发布目录中运行本脚本."
    set "T_STEP2=[1/3] 清理旧版安装 (如有)..."
    set "T_LEGACY_FOUND=  检测到旧版复制安装于 %LOCALAPPDATA%\gdpm, 正在移除..."
    set "T_LEGACY_DONE=  旧版安装已清理."
    set "T_STEP2_DONE=  完成."
    set "T_STEP3=[2/3] 配置用户 PATH..."
    set "T_PATH_ADDED=  已加入用户 PATH"
    set "T_PATH_EXISTS=  已在用户 PATH 中"
    set "T_STEP4=[3/3] 创建配置目录..."
    set "T_CREATED=  已创建"
    set "T_EXISTS=  已存在"
    set "T_VERIFY=  ✓ 验证通过:"
    set "T_VERIFY_ERR=  ⚠ 无法运行 gdpm.exe, 请检查依赖"
    set "T_LANG_SET=  ✓ 已将 gdpm 界面语言设置为中文."
    set "T_LANG_ERR=  ⚠ 未能写入语言设置, 可稍后手动执行: gdpm config set language zh"
    set "T_DONE=安装完成!"
    set "T_KEEP=  ⚠ 请勿删除或移动本目录 (gdpm 从此处运行). 卸载请运行 uninstall."
    set "T_RESTART=请重新打开终端, 然后运行:"
) else (
    set "T_TITLE=gdpm Installer - Windows"
    set "T_PLAN=This script will:"
    set "T_ITEM1=- Add this folder to user PATH: %SOURCE_DIR% (no copy, no admin)"
    set "T_ITEM2=- Create config directory at ~/.gdpm"
    set "T_WHY_HEAD=Why it installs this way:"
    set "T_WHY1=  Same as Linux/macOS: gdpm runs in place from this folder,"
    set "T_WHY2=  no second copy is made. Do NOT delete or move it."
    set "T_WARRANTY=By continuing, you acknowledge that this software is provided as-is without warranty of any kind."
    set "T_CONFIRM=Do you want to proceed? (y/n): "
    set "T_CANCELLED=Installation cancelled."
    set "T_ERR_EXE=Error: gdpm.exe not found. Run this script from the release directory."
    set "T_STEP2=[1/3] Cleaning up legacy install (if any)..."
    set "T_LEGACY_FOUND=  Legacy copy install found at %LOCALAPPDATA%\gdpm, removing..."
    set "T_LEGACY_DONE=  Legacy install cleaned."
    set "T_STEP2_DONE=  Done."
    set "T_STEP3=[2/3] Configuring user PATH..."
    set "T_PATH_ADDED=  Added to user PATH"
    set "T_PATH_EXISTS=  Already in user PATH"
    set "T_STEP4=[3/3] Creating config directory..."
    set "T_CREATED=  Created"
    set "T_EXISTS=  Already exists"
    set "T_VERIFY=  ✓ Verified:"
    set "T_VERIFY_ERR=  ⚠ Cannot run gdpm.exe, please check dependencies"
    set "T_LANG_SET="
    set "T_LANG_ERR="
    set "T_DONE=Installation complete!"
    set "T_KEEP=  ⚠ Do NOT delete or move this folder (gdpm runs from here). Run uninstall to remove."
    set "T_RESTART=Restart your terminal, then run:"
)

echo ============================================
echo  !T_TITLE!
echo ============================================
echo.
echo   !T_PLAN!
echo   !T_ITEM1!
echo   !T_ITEM2!
echo.
echo   !T_WHY_HEAD!
echo   !T_WHY1!
echo   !T_WHY2!
echo.
echo   !T_WARRANTY!
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

if not exist "%SOURCE_DIR%\gdpm.exe" (
    echo   !T_ERR_EXE!
    goto fail
)

rem ===== 旧版复制安装清理 (新版不再复制文件) =====
echo !T_STEP2!
if exist "%LEGACY_DIR%\gdpm.exe" (
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
)
echo !T_STEP2_DONE!

rem ===== 写用户 PATH (HKCU, 当前用户可写, 永不触发 UAC) =====
echo !T_STEP3!
set "CUR_PATH="
for /f "skip=2 tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "CUR_PATH=%%B"
set "PATH_ACTION="
set "NEW_PATH="
if defined CUR_PATH (
    echo !CUR_PATH! | findstr /I /C:"%SOURCE_DIR%" >nul
    if errorlevel 1 (
        set "NEW_PATH=!CUR_PATH!;%SOURCE_DIR%"
        set "PATH_ACTION=added"
    ) else (
        set "PATH_ACTION=exists"
    )
) else (
    set "NEW_PATH=%SOURCE_DIR%"
    set "PATH_ACTION=added"
)
if defined NEW_PATH reg add "HKCU\Environment" /v Path /t REG_EXPAND_SZ /d "!NEW_PATH!" /f >nul
if "!PATH_ACTION!"=="added" (echo !T_PATH_ADDED!) else (echo !T_PATH_EXISTS!)

rem ===== 广播环境变量变更, 让新开终端立即可见 =====
set "GDPM_PS=%TEMP%\gdpm_broadcast.ps1"
>"!GDPM_PS!" echo Add-Type -Name GdpmEnv -Namespace Win32 -MemberDefinition '[DllImport("user32.dll", SetLastError=true, CharSet=CharSet.Auto)] public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);'
>>"!GDPM_PS!" echo $r = [UIntPtr]::Zero
>>"!GDPM_PS!" echo [Win32.GdpmEnv]::SendMessageTimeout([IntPtr]0xffff, 0x1A, [UIntPtr]::Zero, "Environment", 2, 5000, [ref]$r) ^| Out-Null
powershell -NoProfile -ExecutionPolicy Bypass -File "!GDPM_PS!" >nul 2>&1
del "!GDPM_PS!" >nul 2>&1

rem ===== 记录安装位置, 供卸载使用 =====
echo dir=!SOURCE_DIR!>"%MARKER%"

echo !T_STEP4!
if not exist "%USERPROFILE%\.gdpm" (
    mkdir "%USERPROFILE%\.gdpm"
    echo !T_CREATED!
) else (
    echo !T_EXISTS!
)

set "GDPM_VER="
"%SOURCE_DIR%\gdpm.exe" --version > "%TEMP%\gdpm_ver.txt" 2>nul
if errorlevel 1 (
    echo !T_VERIFY_ERR!
) else (
    set /p GDPM_VER=<"%TEMP%\gdpm_ver.txt"
    echo !T_VERIFY! !GDPM_VER!
)
del "%TEMP%\gdpm_ver.txt" >nul 2>&1

rem ===== 中文安装才单独配置默认语言 =====
rem 语言设置以配置文件内容为准判断成败, 不看退出码: 写入发生在输出之前,
rem 而中文 Windows 下 Rich 打印可能因编码问题崩溃返回退出码 1,
rem cmd 管道也不传递退出码, 故用单条 findstr 正则判定配置
if /I "!LANG_CHOICE!"=="zh" (
    "%SOURCE_DIR%\gdpm.exe" config set language zh >nul 2>&1
    findstr /R /C:"language.*zh" "%USERPROFILE%\.gdpm\config.toml" >nul 2>&1
    if not errorlevel 1 (echo !T_LANG_SET!) else (echo !T_LANG_ERR!)
)

echo.
echo ============================================
echo  !T_DONE!
echo  !T_KEEP!
echo  !T_RESTART!
echo    gdpm --help
echo    uninstall
echo ============================================
goto finish

:usage
echo Usage:   install.bat [--lang en^|zh] [-y^|--yes]
echo 用法:    install.bat [--lang en^|zh] [-y^|--yes]
exit /b 0

:usage_error
echo Usage:   install.bat [--lang en^|zh] [-y^|--yes]
echo 用法:    install.bat [--lang en^|zh] [-y^|--yes]
exit /b 1

:fail
if not defined ASSUME_YES pause
exit /b 1

:finish
if not defined ASSUME_YES pause
exit /b 0
