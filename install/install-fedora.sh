#!/usr/bin/env bash
# Fedora. Run from a clone: ./install/install-fedora.sh
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

sudo dnf install -y playerctl pipewire-utils pipx python3
install_baldwin
