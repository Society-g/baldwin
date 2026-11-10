#!/usr/bin/env bash
# One entry point: detects your distro and runs the matching installer.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if [ -r /etc/os-release ]; then . /etc/os-release; fi
ids=" ${ID:-} ${ID_LIKE:-} "

case "$ids" in
  *" nixos "*)                        script=install-nix.sh ;;
  *" arch "*)                         script=install-arch.sh ;;
  *" fedora "*|*" rhel "*)            script=install-fedora.sh ;;
  *" ubuntu "*|*" debian "*)          script=install-ubuntu.sh ;;
  *) if command -v nix >/dev/null; then script=install-nix.sh
     else echo "Unsupported distro (${ID:-unknown}). See the manual install in README.md."; exit 1; fi ;;
esac

echo "Detected: ${PRETTY_NAME:-$ids} -> install/$script"
exec "./install/$script"
