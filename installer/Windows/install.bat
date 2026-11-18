@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "INSTALL_DIR=%LOCALAPPDATA%\gdpm"
set "SRC=%~dp0"
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
    set "T_TITLE=gdpm 安装程序 - Windows"
    set "T_PLAN=本脚本将执行以下操作:"
    set "T_ITEM1=- 安装 gdpm 到 %LOCALAPPDATA%\gdpm"
    set "T_ITEM2=- 将 gdpm 加入用户 PATH"
    set "T_ITEM3=- 创建配置目录 ~/.gdpm"
    set "T_ITEM4=- 检查运行库依赖"
    set "T_WARRANTY=继续即表示你知晓: 本软件按现状提供, 不附带任何担保."
    set "T_CONFIRM=是否继续? 输入 y 或 是: "
    set "T_CANCELLED=已取消安装."
    set "T_ERR_EXE=错误: 未找到 gdpm.exe, 请在解压后的发布目录中运行本脚本."
    set "T_STEP1=[1/4] 检查运行库依赖..."
    set "T_VC_OK=  运行库: 正常"
    set "T_VC_MISS=  [警告] 未检测到 Visual C++ 运行库."
    set "T_VC_REQ=  gdpm 在 Windows 上运行需要该运行库."
    set "T_VC_ASK=  是否现在下载并安装? 输入 y 或 是: "
    set "T_VC_DOWNLOADING=  正在下载运行库..."
    set "T_VC_INSTALLING=  正在安装..."
    set "T_VC_DONE=  完成."
    set "T_VC_FAIL=  [错误] 下载失败, 请手动安装:"
    set "T_VC_MANUAL=  请先手动安装运行库:"
    set "T_STEP2=[2/4] 安装文件..."
    set "T_STEP2_DONE=  完成."
    set "T_STEP3=[3/4] 配置 PATH..."
    set "T_PATH_ADDED=  已加入 PATH"
    set "T_PATH_EXISTS=  已在 PATH 中"
    set "T_STEP4=[4/4] 创建配置目录..."
    set "T_CREATED=  已创建"
    set "T_EXISTS=  已存在"
    set "T_VERIFY=  ✓ 验证通过:"
    set "T_VERIFY_ERR=  ⚠ 无法运行 gdpm.exe, 请检查依赖"
    set "T_LANG_SET=  ✓ 已将 gdpm 界面语言设置为中文."
    set "T_LANG_ERR=  ⚠ 未能写入语言设置, 可稍后手动执行: gdpm config set language zh"
    set "T_DONE=安装完成!"
    set "T_RESTART=请重新打开终端, 然后运行:"
) else (
    set "T_TITLE=gdpm Installer - Windows"
    set "T_PLAN=This script will:"
    set "T_ITEM1=- Install gdpm to %LOCALAPPDATA%\gdpm"
    set "T_ITEM2=- Add gdpm to your user PATH"
    set "T_ITEM3=- Create config directory at ~/.gdpm"
    set "T_ITEM4=- Check runtime dependencies"
    set "T_WARRANTY=By continuing, you acknowledge that this software is provided as-is without warranty of any kind."
    set "T_CONFIRM=Do you want to proceed? type y or yes: "
    set "T_CANCELLED=Installation cancelled."
    set "T_ERR_EXE=Error: gdpm.exe not found. Run this script from the release directory."
    set "T_STEP1=[1/4] Checking runtime dependencies..."
    set "T_VC_OK=  VC++ Redistributable: OK"
    set "T_VC_MISS=  [WARNING] Visual C++ Redistributable not found."
    set "T_VC_REQ=  gdpm requires it to run on Windows."
    set "T_VC_ASK=  Download and install now? type y or yes: "
    set "T_VC_DOWNLOADING=  Downloading VC++ Redistributable..."
    set "T_VC_INSTALLING=  Installing..."
    set "T_VC_DONE=  Done."
    set "T_VC_FAIL=  [ERROR] Download failed. Please install manually:"
    set "T_VC_MANUAL=  Please install manually before running gdpm:"
    set "T_STEP2=[2/4] Installing files..."
    set "T_STEP2_DONE=  Done."
    set "T_STEP3=[3/4] Configuring PATH..."
    set "T_PATH_ADDED=  Added to PATH"
    set "T_PATH_EXISTS=  Already in PATH"
    set "T_STEP4=[4/4] Creating config directory..."
    set "T_CREATED=  Created"
    set "T_EXISTS=  Already exists"
    set "T_VERIFY=  ✓ Verified:"
    set "T_VERIFY_ERR=  ⚠ Cannot run gdpm.exe, please check dependencies"
    set "T_LANG_SET="
    set "T_LANG_ERR="
    set "T_DONE=Installation complete!"
    set "T_RESTART=Restart your terminal, then run:"
)

echo ============================================
echo  !T_TITLE!
echo ============================================
echo.
echo   !T_PLAN!
echo   !T_ITEM1!
echo   !T_ITEM2!
echo   !T_ITEM3!
echo   !T_ITEM4!
echo.
echo   !T_WARRANTY!
echo.

if not defined ASSUME_YES (
    set /p "CONFIRM=  !T_CONFIRM!"
    if not defined CONFIRM set "CONFIRM=n"
    if /I not "!CONFIRM!"=="y" if /I not "!CONFIRM!"=="yes" if not "!CONFIRM!"=="是" if not "!CONFIRM!"=="确认" (
        echo   !T_CANCELLED!
        goto finish
    )
)
echo.

if not exist "%SRC%gdpm.exe" (
    echo   !T_ERR_EXE!
    goto fail
)

echo !T_STEP1!
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" >nul 2>&1
if errorlevel 1 (
    echo !T_VC_MISS!
    echo !T_VC_REQ!
    if defined ASSUME_YES (
        echo !T_VC_MANUAL!
        echo   https://aka.ms/vs/17/release/vc_redist.x64.exe
    ) else (
        set /p "INSTALL_VC=!T_VC_ASK!"
        if /I "!INSTALL_VC!"=="y" (
            echo !T_VC_DOWNLOADING!
            curl -L -o "%TEMP%\vc_redist.x64.exe" "https://aka.ms/vs/17/release/vc_redist.x64.exe"
            if errorlevel 1 (
                echo !T_VC_FAIL!
                echo   https://aka.ms/vs/17/release/vc_redist.x64.exe
            ) else (
                echo !T_VC_INSTALLING!
                "%TEMP%\vc_redist.x64.exe" /install /quiet /norestart
                del "%TEMP%\vc_redist.x64.exe" >nul 2>&1
                echo !T_VC_DONE!
            )
        ) else (
            echo !T_VC_MANUAL!
            echo   https://aka.ms/vs/17/release/vc_redist.x64.exe
        )
    )
) else (
    echo !T_VC_OK!
)

echo !T_STEP2!
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if exist "%INSTALL_DIR%\_internal" rmdir /S /Q "%INSTALL_DIR%\_internal"
copy /Y "%SRC%gdpm.exe" "%INSTALL_DIR%\" >nul
if exist "%SRC%_internal\" xcopy /E /Y /I /Q "%SRC%_internal" "%INSTALL_DIR%\_internal\" >nul
if exist "%SRC%install.bat" copy /Y "%SRC%install.bat" "%INSTALL_DIR%\" >nul 2>nul
if exist "%SRC%uninstall.bat" copy /Y "%SRC%uninstall.bat" "%INSTALL_DIR%\" >nul 2>nul
echo !T_STEP2_DONE!

echo !T_STEP3!
set "CUR_PATH="
for /f "skip=2 tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "CUR_PATH=%%B"
set "PATH_ACTION="
if defined CUR_PATH (
    echo !CUR_PATH! | findstr /I /C:"%INSTALL_DIR%" >nul
    if errorlevel 1 (
        set "NEW_PATH=!CUR_PATH!;%INSTALL_DIR%"
        set "PATH_ACTION=added"
    ) else (
        set "PATH_ACTION=exists"
    )
) else (
    set "NEW_PATH=%INSTALL_DIR%"
    set "PATH_ACTION=added"
)
if defined NEW_PATH reg add "HKCU\Environment" /v Path /t REG_EXPAND_SZ /d "!NEW_PATH!" /f >nul
if "!PATH_ACTION!"=="added" (echo !T_PATH_ADDED!) else (echo !T_PATH_EXISTS!)

echo !T_STEP4!
if not exist "%USERPROFILE%\.gdpm" (
    mkdir "%USERPROFILE%\.gdpm"
    echo !T_CREATED!
) else (
    echo !T_EXISTS!
)

set "GDPM_VER="
"%INSTALL_DIR%\gdpm.exe" --version > "%TEMP%\gdpm_ver.txt" 2>nul
if errorlevel 1 (
    echo !T_VERIFY_ERR!
) else (
    set /p GDPM_VER=<"%TEMP%\gdpm_ver.txt"
    echo !T_VERIFY! !GDPM_VER!
)
del "%TEMP%\gdpm_ver.txt" >nul 2>&1

if /I "!LANG_CHOICE!"=="zh" (
    "%INSTALL_DIR%\gdpm.exe" config set language zh >nul 2>&1
    if errorlevel 1 (echo !T_LANG_ERR!) else (echo !T_LANG_SET!)
)

echo.
echo ============================================
echo  !T_DONE!
echo  !T_RESTART!
echo    gdpm --help
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
