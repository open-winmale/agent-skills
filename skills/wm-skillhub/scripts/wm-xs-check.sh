#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
exec python3 "$ROOT/wm-xs/scripts/wm_xs_check.py" "$@"
