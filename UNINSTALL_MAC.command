#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
python3 "$ROOT/uninstall.py" "$@"
read -r -p "Press Enter to close..." _
