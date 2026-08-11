#!/usr/bin/env python3
"""Unit tests for Agent local XS ref expansion + dep closure (_wm_runtime)."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from _wm_runtime import (
    collect_xs_deps,
    expand_xs_refs,
    resolve_xs_ref,
    workspace_home,
    xs_home,
)


class ExpandXsRefsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        self.ws = self.root / "workspace"
        self.pack = self.root / "skills" / "wm-backtest" / "examples" / "xs" / "demo"
        (self.ws / "scripts").mkdir(parents=True)
        (self.ws / "projects" / "backtest" / "demo").mkdir(parents=True)
        self.pack.mkdir(parents=True)
        (self.ws / "scripts" / "helper.xs").write_text("return 9\n", encoding="utf-8")
        (self.ws / "scripts" / "main.xs").write_text(
            'xs.require("helper.xs")\nreturn 1\n', encoding="utf-8"
        )
        (self.ws / "projects" / "backtest" / "demo" / "trading.xs").write_text(
            "return 1\n", encoding="utf-8"
        )
        (self.pack / "trading.xs").write_text("return 2\n", encoding="utf-8")
        (self.root / "cwd_file.xs").write_text("return 3\n", encoding="utf-8")
        self._old_ws = os.environ.get("WM_WORKSPACE_HOME")
        self._old_xs = os.environ.get("WM_XS_HOME")
        os.environ["WM_WORKSPACE_HOME"] = str(self.ws)
        os.environ.pop("WM_XS_HOME", None)

    def tearDown(self) -> None:
        if self._old_ws is None:
            os.environ.pop("WM_WORKSPACE_HOME", None)
        else:
            os.environ["WM_WORKSPACE_HOME"] = self._old_ws
        if self._old_xs is None:
            os.environ.pop("WM_XS_HOME", None)
        else:
            os.environ["WM_XS_HOME"] = self._old_xs
        self._td.cleanup()

    def test_xs_home_is_workspace(self) -> None:
        self.assertEqual(xs_home(), self.ws)
        self.assertEqual(workspace_home(), self.ws)

    def test_expand_xs_scripts(self) -> None:
        out = expand_xs_refs(
            {"trading": "@xs:scripts/helper.xs", "n": 1},
            cwd=self.root,
            skills_root=self.root / "skills",
        )
        self.assertEqual(out["trading"], "return 9\n")
        self.assertEqual(out["n"], 1)

    def test_legacy_backtest_maps_to_projects(self) -> None:
        path = resolve_xs_ref("@xs:backtest/demo/trading.xs", cwd=self.root)
        self.assertTrue(str(path).endswith("projects/backtest/demo/trading.xs"))

    def test_expand_file_relative(self) -> None:
        out = expand_xs_refs(
            "@file:cwd_file.xs",
            cwd=self.root,
            skills_root=self.root / "skills",
        )
        self.assertEqual(out, "return 3\n")

    def test_expand_pack(self) -> None:
        out = expand_xs_refs(
            "@pack:wm-backtest/examples/xs/demo/trading.xs",
            cwd=self.root,
            skills_root=self.root / "skills",
        )
        self.assertEqual(out, "return 2\n")

    def test_non_ref_unchanged(self) -> None:
        s = 'xs.require("init.xs")\nreturn 1'
        self.assertEqual(expand_xs_refs(s, cwd=self.root), s)

    def test_reject_xs_dotdot(self) -> None:
        with self.assertRaises(ValueError):
            resolve_xs_ref("@xs:../secrets.xs", cwd=self.root)

    def test_reject_pack_dotdot(self) -> None:
        with self.assertRaises(ValueError):
            resolve_xs_ref(
                "@pack:wm-backtest/../../etc/passwd",
                cwd=self.root,
                skills_root=self.root / "skills",
            )

    def test_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            expand_xs_refs("@xs:scripts/missing.xs", cwd=self.root)

    def test_collect_deps(self) -> None:
        deps = collect_xs_deps(self.ws / "scripts" / "main.xs", workspace=self.ws)
        self.assertIn("my/scripts/main.xs", deps)
        self.assertIn("my/scripts/helper.xs", deps)
        self.assertEqual(deps["my/scripts/helper.xs"], "return 9\n")


if __name__ == "__main__":
    unittest.main()
