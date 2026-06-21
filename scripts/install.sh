#!/bin/bash
# Install/Reinstall gdpm to pip.
#
# Usage:
#   ./scripts/install.sh          # Install to pip
#   ./scripts/install.sh --dev    # Install in editable mode (auto-update on code change)

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$PROJECT_DIR"

echo "Uninstalling existing gdpm..."
pip uninstall gdpm -y 2>/dev/null || pip3 uninstall godot-gdpm -y 2>/dev/null || true
pip uninstall godot-gdpm -y 2>/dev/null || pip3 uninstall godot-gdpm -y 2>/dev/null || true

case "${1:-}" in
    --dev)
        echo "Installing in editable mode..."
        pip install -e .
        ;;
    *)
        echo "Building and installing..."
        pip install .
        ;;
esac

echo ""
echo "Installed. Test with:"
echo "  gdpm --version"
echo "  gdpm --help"
