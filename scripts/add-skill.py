#!/usr/bin/env python3
"""Add/update ONE skill from the internal SkillHub without a full re-sync.

Useful when the local skillhub checkout is missing sibling skills (full sync
would die on them) or when shipping a single new skill. Reuses sync-from-skillhub
helpers, respects the marketplaces/overrides contract (include allowlist,
external SKILL.md rewrite, leak gates) and refreshes plugin manifests, root
skills/ index, marketplace manifests and SYNC_MANIFEST.json in place.

Usage:
  SKILLHUB_ROOT=/path/to/skillhub python3 scripts/add-skill.py <skill_id>
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SKILLHUB = ROOT.parent / "skillhub"


def load_sync_module():
    spec = importlib.util.spec_from_file_location(
        "sync_from_skillhub", ROOT / "scripts" / "sync-from-skillhub.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    sid = sys.argv[1]
    skillhub = Path(
        __import__("os").environ.get("SKILLHUB_ROOT", str(DEFAULT_SKILLHUB))
    ).resolve()
    src = skillhub / "skills" / sid
    if not src.is_dir():
        print(f"error: missing skill dir: {src}", file=sys.stderr)
        raise SystemExit(1)

    sync = load_sync_module()
    cfg = json.loads((ROOT / "plugins.json").read_text(encoding="utf-8"))
    plugin = next((p for p in cfg["plugins"] if sid in p["skills"]), None)
    if plugin is None:
        print(
            f"error: {sid} not listed in any plugins.json entry; add it first",
            file=sys.stderr,
        )
        raise SystemExit(1)

    manifest = json.loads((ROOT / "SYNC_MANIFEST.json").read_text(encoding="utf-8"))
    plugin_versions: dict[str, str] = dict(manifest.get("plugins") or {})

    # Skill version: catalog > manifest.json > frontmatter fallback.
    ver = None
    catalog_path = skillhub / "catalog.json"
    if catalog_path.is_file():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        ver = next(
            (s.get("version") for s in catalog.get("skills", []) if s.get("id") == sid),
            None,
        )
    if not ver and (src / "manifest.json").is_file():
        ver = json.loads((src / "manifest.json").read_text(encoding="utf-8")).get("version")
    ver = ver or "0.0.0"

    # 1. Copy skill (honors marketplaces/overrides contract when present).
    plugin_dir = ROOT / "plugins" / plugin["id"]
    dst = plugin_dir / "skills" / sid
    sync.copy_skill(src, dst, skillhub)
    print(f"synced {plugin['id']}/{sid}@{ver}")

    # 2. Plugin manifests (bump plugin version to the skill version label).
    plugin["_version"] = ver
    plugin_versions[plugin["id"]] = ver
    author = cfg["author"]
    sync.write_cursor_plugin(plugin_dir, plugin, author, cfg["homepage"])
    sync.write_codex_plugin(plugin_dir, plugin, author)
    sync.write_claude_plugin(plugin_dir, plugin, author)
    sync.write_codebuddy_plugin(plugin_dir, plugin, author, cfg["homepage"])

    # 3. Root skills/ index (union alias for `npx skills add`).
    root_dst = ROOT / "skills" / sid
    if root_dst.exists():
        shutil.rmtree(root_dst)
    shutil.copytree(dst, root_dst)
    print(f"indexed skills/{sid}")

    # 4. Marketplace manifests for all four client families.
    for p in cfg["plugins"]:
        p.setdefault("_version", plugin_versions.get(p["id"], "0.1.0"))
    sync.write_marketplaces(cfg, plugin_versions)

    # 5. SYNC_MANIFEST.json (keep other skills/plugins untouched).
    skills_list = sorted(set(manifest.get("skills") or []) | {sid})
    manifest["plugins"] = plugin_versions
    manifest["skills"] = skills_list
    (ROOT / "SYNC_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote SYNC_MANIFEST.json (skills={len(skills_list)})")


if __name__ == "__main__":
    main()
