#!/usr/bin/env bash
set -euo pipefail

# Reinstall konsave from this local source checkout.
# Usage: ./install-local.sh [--editable]

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

EDITABLE=0
if [[ "${1:-}" == "--editable" || "${1:-}" == "-e" ]]; then
  EDITABLE=1
elif [[ "${1:-}" != "" ]]; then
  echo "Usage: $0 [--editable|-e]" >&2
  exit 2
fi

echo "==> Working directory: $SCRIPT_DIR"

# Detect a *usable* pipx. A leftover ~/.local/bin/pipx script from a previous
# Python version can exist while its module is gone, so `command -v` alone is
# not enough.
PIPX_IMPL=""
if command -v pipx >/dev/null 2>&1 && pipx --version >/dev/null 2>&1; then
  PIPX_IMPL="command"
elif python3 -m pipx --version >/dev/null 2>&1; then
  PIPX_IMPL="module"
elif command -v pipx >/dev/null 2>&1; then
  echo "    WARNING: pipx is broken (its Python module is missing); falling back to pip."
  echo "    To repair pipx, run: python3 -m pip install --user --upgrade pipx"
fi

run_pipx() {
  if [[ "$PIPX_IMPL" == "command" ]]; then
    pipx "$@"
  else
    python3 -m pipx "$@"
  fi
}

echo "==> Uninstalling existing konsave (pip/pipx, if present)..."
# pip (user/system-managed environments may vary; ignore failures if not installed)
python3 -m pip uninstall -y konsave >/dev/null 2>&1 && echo "    Removed pip installation." || echo "    No pip installation found (or could not remove)."
if [[ -n "$PIPX_IMPL" ]]; then
  run_pipx uninstall konsave >/dev/null 2>&1 && echo "    Removed pipx installation." || echo "    No pipx installation found."
else
  echo "    pipx not available; skipping pipx uninstall."
fi

if [[ -n "$PIPX_IMPL" ]]; then
  echo "==> Installing from local source with pipx..."
  if [[ "$EDITABLE" -eq 1 ]]; then
    run_pipx install -e "$SCRIPT_DIR" --force
  else
    run_pipx install "$SCRIPT_DIR" --force
  fi
  run_pipx ensurepath >/dev/null 2>&1 || true
else
  echo "==> pipx not available; installing from local source with pip (--user --break-system-packages)..."
  if [[ "$EDITABLE" -eq 1 ]]; then
    python3 -m pip install --user --break-system-packages --upgrade -e .
  else
    python3 -m pip install --user --break-system-packages --upgrade .
  fi
fi

echo "==> Verifying installation..."
if command -v konsave >/dev/null 2>&1; then
  echo "    konsave: $(command -v konsave)"
  konsave -v || true
else
  echo "    WARNING: 'konsave' not found on PATH."
  echo "    If installed with pip, ensure ~/.local/bin is in PATH."
  echo "    If installed with pipx, run: pipx ensurepath (then restart your shell)."
fi

echo "==> Done."
