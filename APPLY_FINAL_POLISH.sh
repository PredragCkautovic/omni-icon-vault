#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
echo "== Omni Icon Vault 4.1.2 final pre-push polish =="
echo "Repo: $ROOT"
echo
printf '[1/4] Python tests...\n'
python -m unittest discover -s tests -v
printf '\n[2/4] JavaScript syntax...\n'
if command -v node >/dev/null 2>&1; then
  node --check browser/app.js
  echo 'JavaScript: PASS'
else
  echo 'Node.js not installed; skipping JS parser check.'
fi
printf '\n[3/4] Python compile check...\n'
python -m compileall -q install.py uninstall.py omni.py tools scripts tests
echo 'Python compile: PASS'
printf '\n[4/4] Opening current Omni UI...\n'
python omni.py stop >/dev/null 2>&1 || true
python omni.py open
cat <<'EOF'

Final UI checks:
  1. Copy / filter -> SVG only: only SVG-capable icons remain.
  2. Switch to Glyph only: result count/grid changes.
  3. Cards show capability badges and a COPY SVG / COPY GLYPH hint.
  4. The active capability pill appears under the toolbar and × clears it.
  5. Scroll down: format/capability filters stay visible.
  6. Resize narrow/mobile: Copy / filter and Sort controls remain accessible.
  7. Open details: capability badges appear; primary Copy action follows the selected mode.

If these look good, this tree is ready to commit and push as v4.1.2.
EOF
