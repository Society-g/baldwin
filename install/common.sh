# Shared helpers, sourced by the install-*.sh scripts.
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

install_baldwin() {
  command -v pipx >/dev/null || { echo "pipx not found"; exit 1; }
  pipx install --force "$REPO_DIR"
  pipx ensurepath >/dev/null 2>&1 || true
  echo
  echo "Done. Open a new terminal (or run: export PATH=\"\$HOME/.local/bin:\$PATH\") and run: baldwin"
}
