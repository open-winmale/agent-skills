#!/usr/bin/env bash
# Compat: XS fmt lives in sibling wm-xs pack (local, no API).
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FMT="$ROOT/wm-xs/scripts/wm_xs_fmt.py"
if [[ ! -f "$FMT" ]]; then
  FMT="$(cd "$(dirname "$0")/../../wm-xs/scripts" && pwd)/wm_xs_fmt.py"
fi
exec python3 "$FMT" "$@"
