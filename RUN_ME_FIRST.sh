#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
case "$(uname -s)" in
  Darwin) exec "$ROOT/INSTALL_MAC.command" "$@" ;;
  *) exec "$ROOT/INSTALL_LINUX.sh" "$@" ;;
esac
