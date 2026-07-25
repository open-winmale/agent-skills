#!/usr/bin/env python3
"""Project SkillHub packs into this public marketplace repo.

Default source: ../../end/skillhub (sibling under yepless/).
Override: SKILLHUB_ROOT=/path/to/skillhub
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGINS_PATH = ROOT / "plugins.json"
DEFAULT_SKILLHUB = Path("/Users/jerry/yepless/end/skillhub")


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def copy_skill(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    # Only ship agent-facing files; skip local install markers / secrets.
    ignore = shutil.ignore_patterns(
        ".env",
        ".wm-skill-meta.json",
        "__pycache__",
        "*.pyc",
        ".DS_Store",
    )
    shutil.copytree(src, dst, ignore=ignore)


def write_cursor_plugin(plugin_dir: Path, plugin: dict, author: dict, homepage: str) -> None:
    meta = {
        "name": plugin["id"],
        "version": plugin.get("_version", "0.1.0"),
        "description": plugin["description"],
        "author": {"name": author["name"], "email": author.get("email")},
        "homepage": homepage,
        "repository": f"https://github.com/open-winmale/agent-skills",
        "license": "MIT",
        "keywords": plugin.get("keywords", []),
        "logo": "assets/logo.svg",
        "skills": "./skills/",
    }
    path = plugin_dir / ".cursor-plugin" / "plugin.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")


def write_codex_plugin(plugin_dir: Path, plugin: dict, author: dict) -> None:
    meta = {
        "name": plugin["id"],
        "version": plugin.get("_version", "0.1.0"),
        "description": plugin["description"],
        "author": author.get("name", "WinMale"),
        "skills": "./skills/",
    }
    path = plugin_dir / ".codex-plugin" / "plugin.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")


def write_claude_plugin(plugin_dir: Path, plugin: dict, author: dict) -> None:
    # Claude Code plugin manifest (minimal; skills discovered under skills/).
    meta = {
        "name": plugin["id"],
        "version": plugin.get("_version", "0.1.0"),
        "description": plugin["description"],
        "author": {"name": author.get("name", "WinMale")},
    }
    path = plugin_dir / ".claude-plugin" / "plugin.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")


def write_marketplaces(cfg: dict, plugin_versions: dict[str, str]) -> None:
    author = cfg["author"]
    homepage = cfg["homepage"]
    plugins = cfg["plugins"]

    # Cursor
    cursor = {
        "name": "open-winmale",
        "owner": {"name": author["name"], "email": author.get("email")},
        "metadata": {
            "description": "赢麻了（WinMale）官方 Agent Skills 市场",
            "version": "0.1.0",
            "pluginRoot": "plugins",
        },
        "plugins": [
            {
                "name": p["id"],
                "source": p["id"],
                "description": p["description"],
                "version": plugin_versions[p["id"]],
                "keywords": p.get("keywords", []),
                "category": p.get("category", "productivity"),
                "homepage": homepage,
            }
            for p in plugins
        ],
    }
    out = ROOT / ".cursor-plugin" / "marketplace.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cursor, ensure_ascii=False, indent=2) + "\n")

    # Claude
    claude = {
        "name": "open-winmale",
        "owner": {"name": author["name"], "email": author.get("email")},
        "metadata": {"description": "WinMale official agent skills marketplace"},
        "plugins": [
            {
                "name": p["id"],
                "source": f"./plugins/{p['id']}",
                "version": plugin_versions[p["id"]],
                "description": p["description"],
            }
            for p in plugins
        ],
    }
    out = ROOT / ".claude-plugin" / "marketplace.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(claude, ensure_ascii=False, indent=2) + "\n")

    # Codex / ChatGPT desktop
    codex = {
        "name": "open-winmale",
        "interface": {"displayName": "WinMale Agent Skills"},
        "plugins": [
            {
                "name": p["id"],
                "source": {"path": f"./plugins/{p['id']}"},
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "REQUIRED",
                },
                "category": p.get("category", "productivity"),
            }
            for p in plugins
        ],
    }
    out = ROOT / ".agents" / "plugins" / "marketplace.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(codex, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    cfg = json.loads(PLUGINS_PATH.read_text())
    skillhub = Path(
        __import__("os").environ.get("SKILLHUB_ROOT", str(DEFAULT_SKILLHUB))
    ).resolve()
    if not skillhub.is_dir():
        die(f"skillhub root not found: {skillhub}")

    catalog_path = skillhub / "catalog.json"
    catalog = json.loads(catalog_path.read_text()) if catalog_path.exists() else {}
    skills_meta = {s["id"]: s for s in catalog.get("skills", [])}

    plugin_versions: dict[str, str] = {}
    for plugin in cfg["plugins"]:
        pid = plugin["id"]
        skill_ids = plugin["skills"]
        versions = []
        for sid in skill_ids:
            src = skillhub / "skills" / sid
            if not src.is_dir():
                die(f"missing skill dir: {src}")
            vis = (skills_meta.get(sid) or {}).get("visibility", "")
            if vis in ("internal", "deprecated"):
                die(f"refusing to publish {sid} visibility={vis}")
            dst = ROOT / "plugins" / pid / "skills" / sid
            copy_skill(src, dst)
            ver = (skills_meta.get(sid) or {}).get("version")
            if not ver:
                man = json.loads((src / "manifest.json").read_text())
                ver = man.get("version", "0.0.0")
            versions.append(ver)
            print(f"synced {pid}/{sid}@{ver}")

        # Plugin semver: bump when any skill changes; use max skill version as label for now.
        plugin["_version"] = max(versions, key=lambda v: [int(x) for x in v.split(".")])
        plugin_versions[pid] = plugin["_version"]

        plugin_dir = ROOT / "plugins" / pid
        write_cursor_plugin(plugin_dir, plugin, cfg["author"], cfg["homepage"])
        write_codex_plugin(plugin_dir, plugin, cfg["author"])
        write_claude_plugin(plugin_dir, plugin, cfg["author"])

        # Flat skills/ alias at plugin root is already under skills/ — good for discovery.

    write_marketplaces(cfg, plugin_versions)

    # Root-level skills/ for `npx skills add` discovery (union of first-batch skills).
    root_skills = ROOT / "skills"
    if root_skills.exists():
        shutil.rmtree(root_skills)
    root_skills.mkdir()
    seen: set[str] = set()
    for plugin in cfg["plugins"]:
        for sid in plugin["skills"]:
            if sid in seen:
                continue
            seen.add(sid)
            src = ROOT / "plugins" / plugin["id"] / "skills" / sid
            dst = root_skills / sid
            shutil.copytree(src, dst)
            print(f"indexed skills/{sid}")

    manifest = {
        "generated_from": str(skillhub),
        "hub_version": catalog.get("hub_version"),
        "plugins": plugin_versions,
        "skills": sorted(seen),
    }
    (ROOT / "SYNC_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print("wrote marketplace manifests + SYNC_MANIFEST.json")


if __name__ == "__main__":
    main()
