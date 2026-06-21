#!/bin/bash
# Install gdpm in development mode for local testing.
#
# Usage:
#   ./scripts/install-dev.sh              # Install via pipx (recommended)
#   ./scripts/install-dev.sh --editable   # Install in editable mode via uv
#   ./scripts/install-dev.sh --wrapper    # Create shell wrapper script
#   ./scripts/install-dev.sh --uninstall  # Uninstall gdpm

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$PROJECT_DIR"

case "${1:-}" in
    --uninstall)
        echo "Uninstalling gdpm..."
        pip uninstall gdpm -y 2>/dev/null || true
        pipx uninstall gdpm 2>/dev/null || true
        rm -f "$HOME/.local/bin/gdpm-dev" 2>/dev/null || true
        echo "Done."
        ;;
    --editable)
        echo "Syncing project with uv..."
        uv sync
        echo ""
        echo "Installed in virtual environment. Use:"
        echo "  uv run gdpm --version"
        echo "  uv run gdpm --help"
        ;;
    --wrapper)
        echo "Creating wrapper script..."
        mkdir -p "$HOME/.local/bin"
        cat > "$HOME/.local/bin/gdpm-dev" << EOF
#!/bin/bash
cd "$PROJECT_DIR"
uv run gdpm "\$@"
EOF
        chmod +x "$HOME/.local/bin/gdpm-dev"
        echo "Created: $HOME/.local/bin/gdpm-dev"
        echo ""
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            echo "Add to your PATH:"
            echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        fi
        echo ""
        echo "Test with:"
        echo "  gdpm-dev --version"
        echo "  gdpm-dev --help"
        ;;
    *)
        echo "Building and installing gdpm..."
        uv build --wheel 2>&1
        WHEEL=$(ls -t dist/*.whl | head -1)
        echo ""
        echo "Installing $WHEEL via pipx..."
        pipx install --force "$WHEEL" 2>/dev/null || {
            echo "pipx not found, trying pip..."
            pip install "$WHEEL" 2>/dev/null || {
                echo "Failed. Try: ./scripts/install-dev.sh --wrapper"
                exit 1
            }
        }
        echo ""
        echo "Installed. Test with:"
        echo "  gdpm --version"
        echo "  gdpm --help"
        ;;
esac
