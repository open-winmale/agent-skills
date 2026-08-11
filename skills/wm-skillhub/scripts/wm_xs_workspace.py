#!/usr/bin/env python3
"""wm_xs_workspace.py — compat shim → wm_workspace init|path."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wm_workspace import main  # noqa: E402

if __name__ == "__main__":
    # Map legacy: only init|path; rewrite argv if bare.
    if len(sys.argv) == 1:
        sys.argv.append("init")
    main()
