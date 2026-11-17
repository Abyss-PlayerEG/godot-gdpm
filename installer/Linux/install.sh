#!/bin/bash

set -e

INSTALL_DIR="/usr/local/bin"
LINK_NAME="gdpm"
SOURCE="$(cd "$(dirname "$0")" && pwd)/gdpm"
ZSH_COMPLETION_DIR="/usr/local/share/zsh/site-functions"
BASH_COMPLETION_DIR="/usr/local/share/bash-completion/completions"

echo "========================================"
echo "  gdpm Installer (Linux)"
echo "========================================"
echo ""
echo "  This script will:"
echo "  - Make 'gdpm' available as a system command"
echo "  - Create config directory at ~/.config/gdpm"
echo "  - Install shell completions (zsh, bash)"
echo ""
read -rp "  Do you want to proceed? (Yes/No): " CONFIRM
if [[ "$CONFIRM" != "Yes" && "$CONFIRM" != "yes" ]]; then
    echo "  Installation cancelled."
    exit 0
fi

if [ ! -f "$SOURCE" ]; then
    echo "Error: gdpm binary not found at $SOURCE"
    exit 1
fi

chmod +x "$SOURCE"

if [ -w "$INSTALL_DIR" ]; then
    ln -sf "$SOURCE" "$INSTALL_DIR/$LINK_NAME"
else
    sudo ln -sf "$SOURCE" "$INSTALL_DIR/$LINK_NAME"
fi

mkdir -p ~/.config/gdpm

# Install zsh completion
if [ -d "$ZSH_COMPLETION_DIR" ] || mkdir -p "$ZSH_COMPLETION_DIR" 2>/dev/null; then
    "$SOURCE" --completion zsh > "$ZSH_COMPLETION_DIR/_gdpm" 2>/dev/null || true
    echo "  ✓ Installed zsh completion to $ZSH_COMPLETION_DIR/_gdpm"
fi

# Install bash completion
if [ -d "$BASH_COMPLETION_DIR" ] || mkdir -p "$BASH_COMPLETION_DIR" 2>/dev/null; then
    "$SOURCE" --completion bash > "$BASH_COMPLETION_DIR/gdpm" 2>/dev/null || true
    echo "  ✓ Installed bash completion to $BASH_COMPLETION_DIR/gdpm"
fi

echo ""
echo "Installed gdpm to $INSTALL_DIR/$LINK_NAME"
echo "Run 'gdpm --help' to get started"
