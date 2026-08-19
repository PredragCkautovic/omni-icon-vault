#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
echo "== Omni Icon Vault 4.1.3 release hardening =="
echo "Repo: $ROOT"
echo
printf 'VERSION: '; cat VERSION
python - <<'PY'
import json
print('manifest:', json.load(open('manifest.json'))['version'])
PY
echo
python -m unittest discover -s tests -v
python -m compileall -q install.py uninstall.py omni.py tools scripts tests
if command -v node >/dev/null 2>&1; then node --check browser/app.js; fi
echo
echo "PASS: local validation complete."
echo "Next: inspect git diff, commit/push main, then create tag v4.1.3."
