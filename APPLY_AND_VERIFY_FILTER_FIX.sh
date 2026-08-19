#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
echo "== Omni Icon Vault 4.1.2 filter fix =="
echo "Repo: $ROOT"
echo
echo "[1/3] Running tests..."
python -m unittest discover -s tests -v
echo
echo "[2/3] Removing any stale Omni process and opening the current API..."
python omni.py stop || true
python omni.py open
sleep 1
echo
echo "[3/3] Verifying real capability filters against your installed index..."
python tools/verify_copy_filters.py
echo
echo "PASS: now test Copy / filter -> SVG only, Glyph only, HTML only, CSS only in the browser."
