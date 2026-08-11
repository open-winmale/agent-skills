#!/usr/bin/env bash
# Compat: XS tools live in sibling wm-xs pack
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
XS="$ROOT/wm-xs/scripts/wm_xs.py"
if [[ ! -f "$XS" ]]; then
  XS="$(cd "$(dirname "$0")/../../wm-xs/scripts" && pwd)/wm_xs.py"
fi
exec python3 "$XS" "$@"
