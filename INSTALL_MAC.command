#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.10+ is required. Install Python 3, then run this file again."
  read -r -p "Press Enter to close..." _
  exit 1
fi
python3 "$ROOT/install.py" "$@"
echo
read -r -p "Installation finished. Press Enter to close..." _
