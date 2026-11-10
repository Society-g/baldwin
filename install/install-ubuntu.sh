#!/usr/bin/env bash
# Ubuntu / Debian / Mint. Run from a clone: ./install/install-ubuntu.sh
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

sudo apt update
sudo apt install -y playerctl pipewire-bin pipx python3
install_baldwin
