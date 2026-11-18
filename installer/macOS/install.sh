#!/bin/bash
#
# gdpm 安装程序 (macOS) / gdpm installer (macOS)
#
# 用法 / Usage:
#   ./install.sh                  交互式安装 (先选择语言)
#   ./install.sh --lang zh        以中文安装
#   ./install.sh --lang en -y     英文静默安装
#
# 环境变量 / Environment:
#   PREFIX            安装前缀, 默认 /usr/local
#   GDPM_INSTALL_DIR  自定义安装目录 (覆盖 PREFIX/bin)
#   GDPM_INSTALL_LANG 预设语言 (en|zh), 等同于 --lang
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE="$SCRIPT_DIR/gdpm"
LINK_NAME="gdpm"
PREFIX="${PREFIX:-/usr/local}"
INSTALL_DIR="${GDPM_INSTALL_DIR:-$PREFIX/bin}"
ZSH_COMPLETION_DIR="$PREFIX/share/zsh/site-functions"
BASH_COMPLETION_DIR="$PREFIX/share/bash-completion/completions"

LANG_CHOICE="${GDPM_INSTALL_LANG:-}"
ASSUME_YES=0

usage() {
    echo "Usage:   ./install.sh [--lang en|zh] [-y|--yes]"
    echo "用法:    ./install.sh [--lang en|zh] [-y|--yes]"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --lang)
            if [[ $# -lt 2 ]]; then usage; exit 1; fi
            LANG_CHOICE="$2"; shift 2 ;;
        --lang=*) LANG_CHOICE="${1#*=}"; shift ;;
        -y|--yes) ASSUME_YES=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
    esac
done

# 语言归一化 / Normalize language
LANG_LC="$(printf '%s' "$LANG_CHOICE" | tr '[:upper:]' '[:lower:]')"
case "$LANG_LC" in
    zh|zh-cn|zh_cn|cn|中文) LANG_CHOICE="zh" ;;
    en|en-us|en_us|english) LANG_CHOICE="en" ;;
    "") : ;;
    *)
        echo "Unsupported language '$LANG_CHOICE', falling back to English." >&2
        echo "不支持的语言 '$LANG_CHOICE', 已回退到英文." >&2
        LANG_CHOICE="en"
        ;;
esac

# 未指定时交互选择语言 / Prompt for language when not specified
if [[ -z "$LANG_CHOICE" ]]; then
    if [[ -t 0 ]]; then
        echo "========================================"
        echo "  Select language / 选择语言"
        echo "========================================"
        echo "  [1] English (default)"
        echo "  [2] 中文"
        echo ""
        printf "  > "
        read -r reply || reply=""
        case "$reply" in
            2|zh|ZH|中文) LANG_CHOICE="zh" ;;
            *) LANG_CHOICE="en" ;;
        esac
    else
        LANG_CHOICE="en"
    fi
fi

if [[ "$LANG_CHOICE" == "zh" ]]; then
    T_TITLE="gdpm 安装程序 (macOS)"
    T_PLAN="本脚本将执行以下操作:"
    T_ITEM_1="- 移除二进制文件的隔离属性 (Gatekeeper)"
    T_ITEM_2="- 将 gdpm 注册为系统命令"
    T_ITEM_3="- 安装 shell 补全 (zsh, bash)"
    T_ITEM_4="- 创建配置目录 ~/.gdpm"
    T_WARRANTY="继续即表示你知晓: 本软件按\"现状\"提供, 不附带任何担保."
    T_WHY_HEAD="为什么需要以下两步:"
    T_WHY=(
        "  移除隔离属性: 从网络下载的二进制会被 macOS 标记为隔离文件"
        "  (com.apple.quarantine), Gatekeeper 会阻止未签名程序运行."
        "  移除标记后 gdpm 才能正常运行, 该操作仅作用于安装目录内的文件."
        "  管理员权限: 写入 /usr/local/bin 与系统补全目录通常需要管理员"
        "  权限, 仅在目录不可写时通过 sudo 执行, 不会授予任何常驻权限."
    )
    T_CONFIRM="是否继续? (y/n): "
    T_CANCELLED="已取消安装."
    T_ERR_BINARY="错误: 未找到 gdpm 二进制文件: %s"
    T_ERR_CHMOD="错误: 无法为 gdpm 赋予执行权限: %s"
    T_ERR_PLATFORM="错误: 该文件不是 macOS 可执行文件, 可能下载了错误平台的安装包."
    T_UPDATING="检测到已安装版本, 正在更新."
    T_LINKING="正在注册命令到 %s ..."
    T_NEED_SUDO="需要管理员权限, 可能要求输入密码."
    T_COMPL_OK="✓ 已安装 %s 补全: %s"
    T_COMPL_ERR="⚠ 未能安装 %s 补全."
    T_PATH_WARN="⚠ %s 不在 PATH 中. 请执行: export PATH=\"%s:\$PATH\""
    T_VERIFY="✓ 验证通过: %s"
    T_LANG_SET="✓ 已将 gdpm 界面语言设置为中文."
    T_LANG_ERR="⚠ 未能写入语言设置, 可稍后手动执行: gdpm config set language zh"
    T_DONE="安装完成: %s"
    T_HINT="运行 'gdpm --help' 开始使用."
else
    T_TITLE="gdpm Installer (macOS)"
    T_PLAN="This script will:"
    T_ITEM_1="- Remove quarantine attributes from the binary"
    T_ITEM_2="- Make 'gdpm' available as a system command"
    T_ITEM_3="- Install shell completions (zsh, bash)"
    T_ITEM_4="- Create config directory at ~/.gdpm"
    T_WARRANTY="By continuing, you acknowledge that this software"
    T_WARRANTY="$T_WARRANTY is provided as-is without warranty of any kind."
    T_WHY_HEAD="Why these two steps are needed:"
    T_WHY=(
        "  Quarantine removal: binaries downloaded from the internet get the"
        "  com.apple.quarantine attribute; Gatekeeper blocks unsigned apps."
        "  Removing it is required to run gdpm, and only affects files in this"
        "  install directory."
        "  Administrator privileges: writing to /usr/local/bin and system"
        "  completion directories normally requires admin rights."
        "  sudo is used only when those directories are not writable, and it"
        "  grants no persistent privilege."
    )
    T_CONFIRM="Do you want to proceed? (y/n): "
    T_CANCELLED="Installation cancelled."
    T_ERR_BINARY="Error: gdpm binary not found at %s"
    T_ERR_CHMOD="Error: cannot make gdpm executable: %s"
    T_ERR_PLATFORM="Error: not a macOS executable. You may have downloaded"
    T_ERR_PLATFORM="$T_ERR_PLATFORM the wrong platform package."
    T_UPDATING="Existing installation detected, updating."
    T_LINKING="Registering command at %s ..."
    T_NEED_SUDO="Administrator privileges are required; you may be asked for a password."
    T_COMPL_OK="✓ Installed %s completion: %s"
    T_COMPL_ERR="⚠ Failed to install %s completion."
    T_PATH_WARN="⚠ %s is not in PATH. Run: export PATH=\"%s:\$PATH\""
    T_VERIFY="✓ Verified: %s"
    T_LANG_SET=""
    T_LANG_ERR=""
    T_DONE="Installed gdpm to %s"
    T_HINT="Run 'gdpm --help' to get started."
fi

echo "========================================"
echo "  $T_TITLE"
echo "========================================"
echo ""
echo "  $T_PLAN"
echo "  $T_ITEM_1"
echo "  $T_ITEM_2"
echo "  $T_ITEM_3"
echo "  $T_ITEM_4"
echo ""
echo "  $T_WHY_HEAD"
for why_line in "${T_WHY[@]}"; do
    echo "$why_line"
done
echo ""
echo "  $T_WARRANTY"
echo ""

if [[ "$ASSUME_YES" -ne 1 ]]; then
    printf "  %s" "$T_CONFIRM"
    read -r reply || reply=""
    case "$reply" in
        y|Y|yes|Yes|YES|是|确认|好) : ;;
        *) echo "  $T_CANCELLED"; exit 0 ;;
    esac
fi
echo ""

if [[ ! -f "$SOURCE" ]]; then
    printf "  $T_ERR_BINARY\n" "$SOURCE"
    exit 1
fi

if [[ ! -x "$SOURCE" ]]; then
    if ! chmod +x "$SOURCE" 2>/dev/null; then
        printf "  $T_ERR_CHMOD\n" "$SOURCE"
        exit 1
    fi
fi

if command -v file >/dev/null 2>&1; then
    if ! file "$SOURCE" | grep -q "Mach-O"; then
        echo "  $T_ERR_PLATFORM"
        exit 1
    fi
fi

if [[ -e "$INSTALL_DIR/$LINK_NAME" || -L "$INSTALL_DIR/$LINK_NAME" ]]; then
    echo "  $T_UPDATING"
fi

printf "  $T_LINKING\n" "$INSTALL_DIR/$LINK_NAME"

# Remove quarantine attribute to bypass macOS Gatekeeper
xattr -cr "$SCRIPT_DIR" 2>/dev/null || true

if [[ ! -d "$INSTALL_DIR" ]]; then
    echo "  $T_NEED_SUDO"
    sudo mkdir -p "$INSTALL_DIR"
fi

if [[ -w "$INSTALL_DIR" ]]; then
    ln -sf "$SOURCE" "$INSTALL_DIR/$LINK_NAME"
else
    echo "  $T_NEED_SUDO"
    sudo ln -sf "$SOURCE" "$INSTALL_DIR/$LINK_NAME"
fi

mkdir -p "$HOME/.gdpm"

# 安装补全 / Install completion
write_completion() {
    local shell_name="$1" dir="$2" file="$3" out
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir" 2>/dev/null || sudo mkdir -p "$dir"
    fi
    out="$("$SOURCE" --completion "$shell_name" 2>/dev/null || true)"
    if [[ -z "$out" ]]; then
        printf "  $T_COMPL_ERR\n" "$shell_name"
        return 0
    fi
    if [[ -w "$dir" ]]; then
        printf '%s\n' "$out" > "$file"
    else
        printf '%s\n' "$out" | sudo tee "$file" >/dev/null
    fi
    printf "  $T_COMPL_OK\n" "$shell_name" "$file"
}

write_completion zsh "$ZSH_COMPLETION_DIR" "$ZSH_COMPLETION_DIR/_gdpm"
write_completion bash "$BASH_COMPLETION_DIR" "$BASH_COMPLETION_DIR/gdpm"

# 验证安装 / Verify installation
if version_out="$("$INSTALL_DIR/$LINK_NAME" --version 2>/dev/null)"; then
    printf "  $T_VERIFY\n" "$(printf '%s' "$version_out" | head -n 1)"
fi

# 中文界面: 写入 gdpm 语言配置 / Persist language setting for Chinese UI
if [[ "$LANG_CHOICE" == "zh" ]]; then
    if "$INSTALL_DIR/$LINK_NAME" config set language zh >/dev/null 2>&1; then
        echo "  $T_LANG_SET"
    else
        echo "  $T_LANG_ERR"
    fi
fi

case ":$PATH:" in
    *":$INSTALL_DIR:"*) : ;;
    *) printf "  $T_PATH_WARN\n" "$INSTALL_DIR" "$INSTALL_DIR" ;;
esac

echo ""
printf "  $T_DONE\n" "$INSTALL_DIR/$LINK_NAME"
echo "  $T_HINT"
