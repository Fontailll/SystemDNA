#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "==> Installing SystemDNA..."

# --user install: no sudo needed, goes to ~/.local/bin
pip install --break-system-packages --user -e "$PROJECT_DIR"

BIN_DIR="$HOME/.local/bin"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "==> Adding $BIN_DIR to PATH..."

    case "$SHELL" in
        *fish)
            CONFIG="$HOME/.config/fish/config.fish"
            mkdir -p "$(dirname "$CONFIG")"
            if ! grep -q "fish_add_path $BIN_DIR" "$CONFIG" 2>/dev/null; then
                echo "fish_add_path $BIN_DIR" >> "$CONFIG"
            fi
            fish_add_path "$BIN_DIR"
            ;;
        *zsh)
            CONFIG="$HOME/.zshrc"
            if ! grep -q "export PATH=\$PATH:\$BIN_DIR" "$CONFIG" 2>/dev/null; then
                echo "export PATH=\$PATH:$BIN_DIR" >> "$CONFIG"
            fi
            export PATH="$PATH:$BIN_DIR"
            ;;
        *bash)
            CONFIG="$HOME/.bashrc"
            if ! grep -q "export PATH=\$PATH:\$BIN_DIR" "$CONFIG" 2>/dev/null; then
                echo "export PATH=\$PATH:$BIN_DIR" >> "$CONFIG"
            fi
            export PATH="$PATH:$BIN_DIR"
            ;;
    esac
fi

echo ""
echo "==> SystemDNA installed successfully!"
echo ""

# Try to make it available immediately
if command -v systemdna &>/dev/null; then
    systemdna --help
else
    echo "Restart your terminal or run: exec $SHELL"
    echo "Then use: systemdna --help"
fi
