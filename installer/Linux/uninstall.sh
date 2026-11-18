#!/bin/bash
#
# gdpm 卸载程序 (Linux) / gdpm uninstaller (Linux)
#
# 用法 / Usage:
#   ./uninstall.sh                  交互式卸载 (先选择语言)
#   ./uninstall.sh --lang zh        以中文卸载
#   ./uninstall.sh -y               静默卸载
#
set -euo pipefail

LINK_NAME="gdpm"
PREFIX="${PREFIX:-/usr/local}"
INSTALL_DIR="${GDPM_INSTALL_DIR:-$PREFIX/bin}"
ZSH_COMPLETION="$PREFIX/share/zsh/site-functions/_gdpm"
BASH_COMPLETION="$PREFIX/share/bash-completion/completions/gdpm"

LANG_CHOICE="${GDPM_INSTALL_LANG:-}"
ASSUME_YES=0

usage() {
    echo "Usage:   ./uninstall.sh [--lang en|zh] [-y|--yes]"
    echo "用法:    ./uninstall.sh [--lang en|zh] [-y|--yes]"
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
    T_TITLE="gdpm 卸载程序 (Linux)"
    T_CONFIRM="确认卸载 gdpm? (y/n): "
    T_CANCELLED="已取消."
    T_REMOVED="✓ 已移除 %s"
    T_NOT_FOUND="未在 %s 找到 gdpm"
    T_NOT_LINK="⚠ %s 不是本脚本创建的符号链接, 已跳过 (如为其他方式安装请手动卸载)"
    T_COMPL_REMOVED="✓ 已移除 %s 补全"
    T_NEED_SUDO="需要管理员权限, 可能要求输入密码."
    T_DONE="卸载完成. 配置目录 ~/.gdpm 已保留."
    T_DELETE_HINT="如需彻底清理, 请手动删除: rm -rf ~/.gdpm"
else
    T_TITLE="gdpm Uninstaller (Linux)"
    T_CONFIRM="Remove gdpm? (y/n): "
    T_CANCELLED="Cancelled."
    T_REMOVED="✓ Removed %s"
    T_NOT_FOUND="gdpm not found in %s"
    T_NOT_LINK="⚠ %s is not a symlink created by this script; skipped."
    T_NOT_LINK="$T_NOT_LINK Remove it manually if installed another way."
    T_COMPL_REMOVED="✓ Removed %s completion"
    T_NEED_SUDO="Administrator privileges are required; you may be asked for a password."
    T_DONE="Done. Config at ~/.gdpm was preserved."
    T_DELETE_HINT="Delete manually if needed: rm -rf ~/.gdpm"
fi

echo "========================================"
echo "  $T_TITLE"
echo "========================================"
echo ""

if [[ "$ASSUME_YES" -ne 1 ]]; then
    printf "  %s" "$T_CONFIRM"
    read -r reply || reply=""
    case "$reply" in
        y|Y|yes|Yes|YES|是|确认|好) : ;;
        *) echo "  $T_CANCELLED"; exit 0 ;;
    esac
fi

if [[ -L "$INSTALL_DIR/$LINK_NAME" ]]; then
    if [[ -w "$INSTALL_DIR" ]]; then
        rm -f "$INSTALL_DIR/$LINK_NAME"
    else
        echo "  $T_NEED_SUDO"
        sudo rm -f "$INSTALL_DIR/$LINK_NAME"
    fi
    printf "  $T_REMOVED\n" "$INSTALL_DIR/$LINK_NAME"
elif [[ -e "$INSTALL_DIR/$LINK_NAME" ]]; then
    printf "  $T_NOT_LINK\n" "$INSTALL_DIR/$LINK_NAME"
else
    printf "  $T_NOT_FOUND\n" "$INSTALL_DIR"
fi

remove_file() {
    local file="$1" label="$2" dir
    if [[ -f "$file" ]]; then
        dir="$(dirname "$file")"
        if [[ -w "$dir" ]]; then
            rm -f "$file"
        else
            echo "  $T_NEED_SUDO"
            sudo rm -f "$file"
        fi
        printf "  $T_COMPL_REMOVED\n" "$label"
    fi
}

remove_file "$ZSH_COMPLETION" "zsh"
remove_file "$BASH_COMPLETION" "bash"

echo ""
echo "  $T_DONE"
echo "  $T_DELETE_HINT"
