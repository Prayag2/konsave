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

echo "==> Uninstalling existing konsave (pip/pipx, if present)..."
# pip (user/system-managed environments may vary; ignore failures if not installed)
python3 -m pip uninstall -y konsave >/dev/null 2>&1 && echo "    Removed pip installation." || echo "    No pip installation found (or could not remove)."
if command -v pipx >/dev/null 2>&1; then
  pipx uninstall konsave >/dev/null 2>&1 && echo "    Removed pipx installation." || echo "    No pipx installation found."
else
  echo "    pipx not found; skipping pipx uninstall."
fi

if command -v pipx >/dev/null 2>&1; then
  echo "==> Installing from local source with pipx..."
  if [[ "$EDITABLE" -eq 1 ]]; then
    pipx install -e "$SCRIPT_DIR" --force
  else
    pipx install "$SCRIPT_DIR" --force
  fi
  pipx ensurepath >/dev/null 2>&1 || true
else
  echo "==> pipx not found; installing from local source with pip (--user --break-system-packages)..."
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
