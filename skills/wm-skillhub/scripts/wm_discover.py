#!/usr/bin/env python3
"""wm_discover.py — POST /v1/analysis/xs/discover."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _wm_runtime import api_base, post_json_authed, print_result_or_full  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("body", help="'json' or @file.json")
    p.add_argument("--result", action="store_true")
    args = p.parse_args()
    if args.body.startswith("@"):
        raw = Path(args.body[1:]).read_text(encoding="utf-8")
        payload = json.loads(raw)
    else:
        payload = json.loads(args.body)
    skill_dir = Path(__file__).resolve().parent.parent
    url = f"{api_base()}/v1/analysis/xs/discover"
    _status, resp = post_json_authed(url, payload, skill_dir=skill_dir)
    if args.result:
        try:
            d = json.loads(resp)
            data = d.get("data", d)
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception:
            print(resp)
    else:
        print_result_or_full(resp, "full")


if __name__ == "__main__":
    main()
