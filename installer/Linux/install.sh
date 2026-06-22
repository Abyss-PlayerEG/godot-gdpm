#!/bin/bash

set -e

INSTALL_DIR="/usr/local/bin"
LINK_NAME="gdpm"
SOURCE="$(cd "$(dirname "$0")" && pwd)/gdpm"

echo "========================================"
echo "  gdpm Installer (Linux)"
echo "========================================"
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

echo "Installed gdpm to $INSTALL_DIR/$LINK_NAME"
echo "Run 'gdpm --help' to get started"
