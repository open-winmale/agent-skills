#!/usr/bin/env python3
"""wm_skill_run.py — L1 skill run via hub wrapper (auth internal)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _wm_runtime import (  # noqa: E402
    api_base,
    expand_xs_refs,
    post_json_authed,
    print_result_or_full,
    resolve_skills_root,
)


def load_args(spec: str, *, skills_root: Path, cwd: Path) -> tuple[dict, str]:
    """Return (args_body, optional_symbol_from_file)."""
    if spec.startswith("@"):
        raw = Path(spec[1:]).expanduser()
        if not raw.is_absolute():
            raw = cwd / raw
        text = raw.read_text(encoding="utf-8")
    else:
        text = spec
    d = json.loads(text)
    if not isinstance(d, dict):
        raise SystemExit("args must be a JSON object")
    symbol = ""
    if "args" in d and isinstance(d["args"], dict):
        body = d["args"]
        symbol = str(d.get("symbol") or "").strip()
    else:
        body = d
    try:
        body = expand_xs_refs(body, cwd=cwd, skills_root=skills_root)
    except (OSError, ValueError) as e:
        raise SystemExit(f"xs ref expand failed: {e}") from e
    return body, symbol


def main() -> None:
    p = argparse.ArgumentParser(description="Run wm-* skill via Open API")
    p.add_argument("skill_id")
    p.add_argument("args", help="'json' or @file.json")
    p.add_argument("--symbol", default="")
    p.add_argument("--result", action="store_true")
    args = p.parse_args()
    if not re.fullmatch(r"wm-[a-z0-9-]+", args.skill_id):
        raise SystemExit(f"skill_id must look like wm-* (got: {args.skill_id})")
    scripts_dir = Path(__file__).resolve().parent
    skill_dir = scripts_dir.parent
    skills_root = resolve_skills_root(scripts_dir)
    cwd = Path.cwd()
    body_args, file_symbol = load_args(args.args, skills_root=skills_root, cwd=cwd)
    payload: dict = {"args": body_args}
    symbol = args.symbol or file_symbol
    if symbol:
        payload["symbol"] = symbol
    url = f"{api_base()}/v1/skills/{args.skill_id}/run"
    _status, raw = post_json_authed(url, payload, skill_dir=skill_dir)
    print_result_or_full(raw, "result" if args.result else "full")


if __name__ == "__main__":
    main()
