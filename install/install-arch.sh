#!/usr/bin/env bash
# Arch / Manjaro / EndeavourOS. Run from a clone: ./install/install-arch.sh
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

sudo pacman -S --needed --noconfirm playerctl pipewire python-pipx
install_baldwin
