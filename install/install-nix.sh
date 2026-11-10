#!/usr/bin/env bash
# Nix / NixOS (no root needed). Run from a clone: ./install/install-nix.sh
# Builds baldwin and installs a `baldwin` command into your Nix profile.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

command -v nix >/dev/null || { echo "nix not found"; exit 1; }
FEATURES=(--extra-experimental-features "nix-command flakes")
nix "${FEATURES[@]}" profile remove baldwin >/dev/null 2>&1 || true
if ! nix "${FEATURES[@]}" profile add --file "$REPO_DIR/default.nix" 2>/dev/null &&
   ! nix "${FEATURES[@]}" profile install --file "$REPO_DIR/default.nix" 2>/dev/null; then
  nix-env -if "$REPO_DIR/default.nix"   # older nix-env style profiles
fi
echo "Installed. Run: baldwin"
