# Shared helpers, sourced by the install-*.sh scripts.
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

install_baldwin() {
  command -v pipx >/dev/null || { echo "pipx not found"; exit 1; }
  pipx install --force "$REPO_DIR"
  pipx ensurepath >/dev/null 2>&1 || true
  echo
  if PATH="$HOME/.local/bin:$PATH" command -v baldwin >/dev/null; then
    echo "Installed. Open a new terminal (or run: export PATH=\"\$HOME/.local/bin:\$PATH\"), then run: baldwin"
  else
    echo "pipx finished but 'baldwin' was not found; check the output above."
    exit 1
  fi
}
