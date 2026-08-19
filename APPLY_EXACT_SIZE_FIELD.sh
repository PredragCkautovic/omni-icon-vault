#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
echo "== Omni Icon Vault exact preview size field =="
if command -v node >/dev/null 2>&1; then
  echo "[1/3] Checking browser JavaScript..."
  node --check browser/app.js
else
  echo "[1/3] node not installed; skipping JS syntax check"
fi
echo "[2/3] Restarting Omni..."
if command -v omni-icons >/dev/null 2>&1; then
  omni-icons stop >/dev/null 2>&1 || true
  omni-icons start
  echo "[3/3] Opening Omni..."
  omni-icons open
else
  python omni.py stop >/dev/null 2>&1 || true
  python omni.py start
  echo "[3/3] Opening Omni..."
  python omni.py open
fi
echo "Done. Open an icon and use the exact px field beside the Size slider."
