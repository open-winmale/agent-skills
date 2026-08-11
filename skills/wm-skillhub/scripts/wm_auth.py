#!/usr/bin/env python3
"""wm_auth.py — print access_token (or --status). Default omit scope."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _wm_runtime import (  # noqa: E402
    CACHE_FILE,
    get_access_token,
    read_cache_meta,
)


def main() -> None:
    skill_dir = Path(__file__).resolve().parent.parent
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        ok, iso = read_cache_meta()
        if ok:
            print(f"wm-auth: cache=valid expires_at={iso} file={CACHE_FILE}")
            raise SystemExit(0)
        print(f"wm-auth: cache=missing_or_expired file={CACHE_FILE}")
        raise SystemExit(1)
    tok = get_access_token(skill_dir=skill_dir)
    sys.stdout.write(tok)


if __name__ == "__main__":
    main()
