#!/usr/bin/env bash
# wm.sh — unified SkillHub CLI facade for agents.
# Subcommands map to existing thin wrappers (same auth / paths).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cmd="${1:-}"
if [[ $# -gt 0 ]]; then
  shift
fi

usage() {
  cat <<'EOF' >&2
Usage: bash …/wm-skillhub/scripts/wm.sh <command> [args…]

Commands (preferred single entry for agents):
  discover   → wm-discover.sh     POST /v1/analysis/xs/discover
  run        → wm-skill-run.sh    POST /v1/skills/{id}/run   (L1 only)
  xs-eval    → wm-xs-eval.sh      POST /v1/analysis/xs/eval
  xs-check   → wm-xs-check.sh     POST /v1/analysis/xs/check
  xs-fmt     → wm-xs-fmt.sh       local fmt (wm_xs_fmt.py; no API)
  xs         → wm-xs.sh           XS helper (eval|check)
  workspace  → wm-workspace.sh    init|path|pull|push (~/.winmale/workspace)
  xs-workspace → alias of workspace init|path (compat)
  hub        → wm-hub.sh          catalog / install / doctor
  auth       → wm-auth.sh         token only

Examples:
  bash …/wm.sh discover '{"q":"kline.query_bars","domains":["vfunc"],"limit":5}' --result
  bash …/wm.sh run wm-company-card '{}' --symbol 600519 --result
  bash …/wm.sh xs-eval @xs:scripts/demo.xs 600519 --result
  bash …/wm.sh run wm-backtest @request.json --result
      # request.json 字段可用 "@xs:projects/backtest/…/trading.xs" / "@pack:…"
  bash …/wm.sh workspace init
  bash …/wm.sh workspace push scripts
  bash …/wm.sh xs-fmt path.xs

Do NOT: wm.sh run wm-discover | wm-xs | role-*  (not L1 skill_run).
EOF
}

case "$cmd" in
  ""|-h|--help|help)
    usage
    exit 0
    ;;
  discover|disc)
    exec bash "$HERE/wm-discover.sh" "$@"
    ;;
  run|skill-run|skills-run)
    if [[ "${1:-}" == "wm-discover" ]]; then
      echo "wm-discover is not L1 skill_run. Use: bash $HERE/wm.sh discover '<json>' [--result]" >&2
      shift
      exec bash "$HERE/wm-discover.sh" "$@"
    fi
    if [[ "${1:-}" == "wm-xs" || "${1:-}" == "wm-xs-eval-guide" || "${1:-}" == "wm-xs-author-internal" ]]; then
      echo "${1} is not L1 skill_run. Use: bash $HERE/wm.sh xs-eval … / xs-check … / xs-fmt …" >&2
      exit 2
    fi
    if [[ "${1:-}" == role-* ]]; then
      echo "Roles are not runnable via skills/run. Orchestrate allowed_skills with: bash $HERE/wm.sh run <wm-*> …" >&2
      exit 2
    fi
    exec bash "$HERE/wm-skill-run.sh" "$@"
    ;;
  xs-eval|eval)
    exec bash "$HERE/wm-xs-eval.sh" "$@"
    ;;
  xs-check|check)
    exec bash "$HERE/wm-xs-check.sh" "$@"
    ;;
  xs-fmt|fmt)
    exec bash "$HERE/wm-xs-fmt.sh" "$@"
    ;;
  workspace)
    exec bash "$HERE/wm-workspace.sh" "$@"
    ;;
  xs-workspace)
    # Compat: only init|path; prefer `workspace`
    exec bash "$HERE/wm-workspace.sh" "$@"
    ;;
  xs)
    exec bash "$HERE/wm-xs.sh" "$@"
    ;;
  hub)
    exec bash "$HERE/wm-hub.sh" "$@"
    ;;
  auth)
    exec bash "$HERE/wm-auth.sh" "$@"
    ;;
  *)
    echo "unknown command: $cmd" >&2
    usage
    exit 2
    ;;
esac
