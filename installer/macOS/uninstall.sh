#!/bin/bash
set -e

INSTALL_DIR="/usr/local/bin"
LINK_NAME="gdpm"
ZSH_COMPLETION="/usr/local/share/zsh/site-functions/_gdpm"
BASH_COMPLETION="/usr/local/share/bash-completion/completions/gdpm"

echo "========================================"
echo "  gdpm Uninstaller (macOS)"
echo "========================================"
echo ""
read -rp "  Remove gdpm? (y/n): " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "  Cancelled."
    exit 0
fi

if [ -L "$INSTALL_DIR/$LINK_NAME" ]; then
    if [ -w "$INSTALL_DIR" ]; then
        rm "$INSTALL_DIR/$LINK_NAME"
    else
        sudo rm "$INSTALL_DIR/$LINK_NAME"
    fi
    echo "  ✓ Removed $INSTALL_DIR/$LINK_NAME"
else
    echo "  gdpm not found in $INSTALL_DIR"
fi

# Remove shell completions
if [ -f "$ZSH_COMPLETION" ]; then
    if [ -w "$(dirname "$ZSH_COMPLETION")" ]; then
        rm "$ZSH_COMPLETION"
    else
        sudo rm "$ZSH_COMPLETION"
    fi
    echo "  ✓ Removed zsh completion"
fi

if [ -f "$BASH_COMPLETION" ]; then
    if [ -w "$(dirname "$BASH_COMPLETION")" ]; then
        rm "$BASH_COMPLETION"
    else
        sudo rm "$BASH_COMPLETION"
    fi
    echo "  ✓ Removed bash completion"
fi

echo ""
echo "  Done. Config at ~/.config/gdpm was preserved."
echo "  Delete manually if needed: rm -rf ~/.config/gdpm"
