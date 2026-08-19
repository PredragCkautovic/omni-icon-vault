#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
echo "== Omni Icon Vault 4.1.2 sidebar polish =="
echo "Repo: $ROOT"
echo
echo "[1/3] Running tests..."
python -m unittest discover -s tests -v
echo
echo "[2/3] Checking browser JavaScript..."
if command -v node >/dev/null 2>&1; then node --check browser/app.js; else echo "node not installed; skipping JS syntax check"; fi
echo
echo "[3/3] Restarting Omni and opening the refreshed UI..."
python omni.py stop >/dev/null 2>&1 || true
python omni.py open
echo
echo "PASS: sidebar polish applied. If an old tab is open, close it or hard-refresh once."
