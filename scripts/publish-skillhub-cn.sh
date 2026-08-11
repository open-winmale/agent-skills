#!/usr/bin/env bash
# Thin wrapper around publish-skillhub-cn.py
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Prefer repo-local env file without exporting into the shell history
if [[ -f "$ROOT/.env.skillhub.cn" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env.skillhub.cn"
  set +a
fi

if ! command -v skillhub >/dev/null 2>&1 && [[ -x "$HOME/.local/bin/skillhub" ]]; then
  export PATH="$HOME/.local/bin:$PATH"
fi

exec python3 "$ROOT/scripts/publish-skillhub-cn.py" "$@"
