#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.10+ is required. Install Python 3, then rerun this script." >&2
  exit 1
fi
exec python3 "$ROOT/install.py" "$@"
