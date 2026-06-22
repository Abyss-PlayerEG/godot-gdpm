#!/bin/bash

set -e

INSTALL_DIR="/usr/local/bin"
LINK_NAME="gdpm"
SOURCE="$(cd "$(dirname "$0")" && pwd)/gdpm"

echo "========================================"
echo "  gdpm Installer (macOS)"
echo "========================================"
echo ""
echo "  This script will:"
echo "  - Remove quarantine attributes from the binary"
echo "  - Make 'gdpm' available as a system command"
echo "  - Create config directory at ~/.config/gdpm"
echo ""
echo "  By continuing, you acknowledge that this software"
echo "  is provided as-is without warranty of any kind."
echo ""
read -rp "  Do you want to proceed? (Yes/No): " CONFIRM
if [[ "$CONFIRM" != "Yes" && "$CONFIRM" != "yes" ]]; then
    echo "  Installation cancelled."
    exit 0
fi
echo ""

if [ ! -f "$SOURCE" ]; then
    echo "Error: gdpm binary not found at $SOURCE"
    exit 1
fi

# Remove quarantine attribute to bypass macOS Gatekeeper
xattr -cr "$(dirname "$SOURCE")" 2>/dev/null || true

if [ -w "$INSTALL_DIR" ]; then
    ln -sf "$SOURCE" "$INSTALL_DIR/$LINK_NAME"
else
    sudo ln -sf "$SOURCE" "$INSTALL_DIR/$LINK_NAME"
fi

mkdir -p ~/.config/gdpm

echo "Installed gdpm to $INSTALL_DIR/$LINK_NAME"
echo "Run 'gdpm --help' to get started"
