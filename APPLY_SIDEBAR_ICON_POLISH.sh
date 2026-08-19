#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
echo "Applying Omni sidebar icon polish..."
python -m py_compile tools/omni_server.py omni.py >/dev/null 2>&1 || true
if command -v omni-icons >/dev/null 2>&1; then
  omni-icons stop >/dev/null 2>&1 || true
fi
python omni.py start >/dev/null 2>&1 || true
python omni.py open >/dev/null 2>&1 || true
echo "Done. If the browser was already open, do a hard refresh (Ctrl+Shift+R)."
