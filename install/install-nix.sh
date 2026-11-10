#!/usr/bin/env bash
# Nix / NixOS (no root needed). Run from a clone: ./install/install-nix.sh
# Copies the project to ~/.local/share/baldwin and puts a `baldwin` launcher in ~/.local/bin.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

command -v nix-shell >/dev/null || { echo "nix-shell not found"; exit 1; }
dest="$HOME/.local/share/baldwin"
mkdir -p "$dest" "$HOME/.local/bin"
cp -r "$REPO_DIR"/baldwin "$REPO_DIR"/shell.nix "$dest"/
cat > "$HOME/.local/bin/baldwin" <<LAUNCH
#!/bin/sh
cd "$dest" && exec nix-shell --run "python -m baldwin"
LAUNCH
chmod +x "$HOME/.local/bin/baldwin"
echo "Installed. Make sure ~/.local/bin is on your PATH, then run: baldwin"
echo "(first launch downloads dependencies and may take a minute)"
