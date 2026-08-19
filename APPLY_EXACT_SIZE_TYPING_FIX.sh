#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
echo "== Omni Icon Vault 4.1.2 exact-size typing fix =="
if command -v node >/dev/null 2>&1; then
  node --check browser/app.js
fi
python -m py_compile tools/omni_server.py >/dev/null 2>&1 || true
if command -v omni-icons >/dev/null 2>&1; then
  omni-icons stop >/dev/null 2>&1 || true
  omni-icons start >/dev/null 2>&1 || true
  omni-icons open >/dev/null 2>&1 || true
else
  python omni.py stop >/dev/null 2>&1 || true
  python omni.py start >/dev/null 2>&1 || true
  python omni.py open >/dev/null 2>&1 || true
fi
echo "Applied. Focus the size field, type an exact value, then Enter or click away to commit."
