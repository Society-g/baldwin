#!/usr/bin/env bash
# Removes the `baldwin` command, however it was installed (pipx or Nix).
#   ./uninstall.sh           remove the program
#   ./uninstall.sh --purge   also delete baldwin's cache and config (~/.cache/baldwin, ~/.config/baldwin)
# System packages (playerctl, pipewire, pipx) are left alone since other programs may use them.
set -uo pipefail

purge=0
[ "${1:-}" = "--purge" ] && purge=1
removed=0

if command -v pipx >/dev/null; then
  listed="$(pipx list --short 2>/dev/null || true)"  # captured, so grep -q can't SIGPIPE it
  if grep -q '^baldwin ' <<<"$listed"; then
    pipx uninstall baldwin && removed=1
  fi
fi

if command -v nix >/dev/null; then
  FEATURES=(--extra-experimental-features "nix-command flakes")
  profiled="$(nix "${FEATURES[@]}" profile list 2>/dev/null || true)"
  envs="$(command -v nix-env >/dev/null && nix-env -q 2>/dev/null || true)"
  if grep -q 'Name:.*baldwin' <<<"$profiled"; then
    nix "${FEATURES[@]}" profile remove baldwin && removed=1
  elif grep -q '^baldwin' <<<"$envs"; then
    nix-env -e baldwin && removed=1
  fi
fi

# Leftovers from the older Nix installer: a launcher script plus a copy of the source.
launcher="$HOME/.local/bin/baldwin"
if [ -f "$launcher" ] && grep -q 'python -m baldwin' "$launcher" 2>/dev/null; then
  rm -f "$launcher" && removed=1
fi
[ -d "$HOME/.local/share/baldwin" ] && rm -rf "$HOME/.local/share/baldwin" && removed=1

if [ "$purge" = 1 ]; then
  rm -rf "${XDG_CACHE_HOME:-$HOME/.cache}/baldwin" "${XDG_CONFIG_HOME:-$HOME/.config}/baldwin"
  echo "Removed baldwin's cache and config."
fi

if [ "$removed" = 1 ]; then
  echo "baldwin uninstalled."
else
  echo "Nothing to uninstall: baldwin wasn't installed with pipx or Nix."
fi
