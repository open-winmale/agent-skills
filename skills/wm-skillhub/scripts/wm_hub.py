#!/usr/bin/env python3
"""wm_hub.py — SkillHub pack lifecycle (list/install/update/enable/disable/rename/cleanup/doctor)."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _wm_runtime import WINMALE_HOME, USER_ENV, eprint, skills_root_from_hub_scripts  # noqa: E402

ALIAS_FILE = "aliases.json"
DISABLED_FILE = ".wm-disabled"
KNOWN_ALIASES = {
    "wm-xs-eval-guide": "wm-xs",
}


def open_base() -> str:
    return (os.environ.get("WINMALE_OPEN_BASE") or "https://open.winmale.com").rstrip("/")


def skills_root() -> Path:
    env = os.environ.get("WM_SKILLS_ROOT", "").strip()
    if env:
        return Path(env)
    return skills_root_from_hub_scripts(Path(__file__).resolve().parent)


def aliases_path(root: Path) -> Path:
    return WINMALE_HOME / "hub" / ALIAS_FILE


def load_aliases(root: Path) -> dict:
    p = aliases_path(root)
    data = dict(KNOWN_ALIASES)
    if p.is_file():
        try:
            data.update(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return data


def save_aliases(root: Path, data: dict) -> None:
    p = aliases_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_id(root: Path, pack_id: str) -> str:
    aliases = load_aliases(root)
    return aliases.get(pack_id, pack_id)


def read_local_version(root: Path, pack_id: str) -> str:
    pack = root / pack_id
    for name in (".wm-skill-meta.json", "manifest.json"):
        f = pack / name
        if f.is_file():
            try:
                return str(json.loads(f.read_text(encoding="utf-8")).get("version") or "")
            except Exception:
                pass
    skill = pack / "SKILL.md"
    if skill.is_file():
        m = re.search(r"^version:\s*[\"']?([^\"'\n]+)", skill.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1).strip()
    return ""


def is_disabled(root: Path, pack_id: str) -> bool:
    return (root / pack_id / DISABLED_FILE).is_file()


def cmd_list(root: Path) -> None:
    aliases = load_aliases(root)
    rows = []
    for p in sorted(root.iterdir()):
        if not p.is_dir():
            continue
        if not (p / "SKILL.md").is_file():
            continue
        pid = p.name
        rows.append(
            {
                "id": pid,
                "version": read_local_version(root, pid),
                "disabled": is_disabled(root, pid),
                "alias_of": None,
            }
        )
    for old, new in aliases.items():
        if (root / old).is_dir():
            continue
        rows.append({"id": old, "version": "", "disabled": False, "alias_of": new})
    print(json.dumps({"skills_root": str(root), "packs": rows}, ensure_ascii=False, indent=2))


def cmd_enable(root: Path, pack_id: str, enable: bool) -> None:
    pack_id = resolve_id(root, pack_id)
    pack = root / pack_id
    if not pack.is_dir():
        raise SystemExit(f"pack not found: {pack_id}")
    marker = pack / DISABLED_FILE
    if enable:
        if marker.exists():
            marker.unlink()
        print(f"enabled {pack_id}")
    else:
        marker.write_text("disabled locally by wm_hub\n", encoding="utf-8")
        print(f"disabled {pack_id}")


def cmd_rename(root: Path, old_id: str, new_id: str, *, keep_alias: bool = True) -> None:
    if not re.fullmatch(r"(wm|role)-[a-z0-9-]+", old_id):
        raise SystemExit(f"bad old id: {old_id}")
    if not re.fullmatch(r"(wm|role)-[a-z0-9-]+", new_id):
        raise SystemExit(f"bad new id: {new_id}")
    src = root / old_id
    dst = root / new_id
    if not src.is_dir():
        # already renamed?
        if dst.is_dir():
            aliases = load_aliases(root)
            aliases[old_id] = new_id
            save_aliases(root, aliases)
            print(f"alias only: {old_id} → {new_id} (target exists)")
            return
        raise SystemExit(f"source pack missing: {src}")
    if dst.exists():
        raise SystemExit(f"target already exists: {dst}")
    src.rename(dst)
    # frontmatter name
    skill = dst / "SKILL.md"
    if skill.is_file():
        text = skill.read_text(encoding="utf-8")
        text2 = re.sub(r"(?m)^name:\s*.*$", f"name: {new_id}", text, count=1)
        if text2 != text:
            skill.write_text(text2, encoding="utf-8")
    meta = dst / ".wm-skill-meta.json"
    if meta.is_file():
        try:
            doc = json.loads(meta.read_text(encoding="utf-8"))
            doc["id"] = new_id
            doc["renamed_from"] = old_id
            doc["renamed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            meta.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except Exception:
            pass
    if keep_alias:
        aliases = load_aliases(root)
        aliases[old_id] = new_id
        save_aliases(root, aliases)
        # stub pointer for agents that still open old path
        stub = root / old_id
        stub.mkdir(parents=True, exist_ok=True)
        (stub / "SKILL.md").write_text(
            f"""---
name: {old_id}
display_name: "（已更名）"
version: 0.0.0-alias
description: 已更名为 {new_id}。请改读 .cursor/skills/{new_id}/SKILL.md。
---

# Alias → `{new_id}`

本目录为过渡别名。请打开 **`{new_id}`** Pack。

```bash
python .cursor/skills/wm-skillhub/scripts/wm_hub.py cleanup
```
""",
            encoding="utf-8",
        )
        (stub / ".wm-alias.json").write_text(
            json.dumps({"alias_of": new_id, "deprecated": True}, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"renamed {old_id} → {new_id}")


def cmd_cleanup(root: Path) -> None:
    removed = []
    for p in list(root.iterdir()):
        if not p.is_dir():
            continue
        alias_meta = p / ".wm-alias.json"
        skill = p / "SKILL.md"
        if alias_meta.is_file():
            try:
                doc = json.loads(alias_meta.read_text(encoding="utf-8"))
                target = doc.get("alias_of")
                if target and (root / target).is_dir():
                    shutil.rmtree(p)
                    removed.append(p.name)
                    continue
            except Exception:
                pass
        if skill.is_file() and "0.0.0-alias" in skill.read_text(encoding="utf-8")[:200]:
            shutil.rmtree(p)
            removed.append(p.name)
    print(json.dumps({"removed": removed}, indent=2))


def cmd_doctor(root: Path) -> None:
    report = {
        "skills_root": str(root),
        "credentials": USER_ENV.is_file(),
        "credentials_path": str(USER_ENV),
        "aliases": load_aliases(root),
        "packs": [],
        "issues": [],
    }
    for p in sorted(root.iterdir()):
        if not p.is_dir() or not (p / "SKILL.md").is_file():
            continue
        pid = p.name
        ver = read_local_version(root, pid)
        report["packs"].append({"id": pid, "version": ver, "disabled": is_disabled(root, pid)})
        if (p / ".wm-alias.json").is_file():
            continue
        if not ver:
            report["issues"].append(f"missing version: {pid}")
    if not report["credentials"]:
        report["issues"].append(f"missing credentials at {USER_ENV}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["issues"]:
        raise SystemExit(1)


def cmd_update(root: Path, only_id: str | None, hub_only: bool) -> None:
    # Delegate to existing shell updater when available
    sh = Path(__file__).resolve().parent / "update-from-catalog.sh"
    if not sh.is_file():
        raise SystemExit("update-from-catalog.sh missing")
    import subprocess

    cmd = ["bash", str(sh)]
    if hub_only:
        cmd.append("--hub-only")
    elif only_id:
        cmd.append(only_id)
    raise SystemExit(subprocess.call(cmd))


def cmd_install(root: Path, pack_id: str) -> None:
    pack_id = resolve_id(root, pack_id)
    url = f"{open_base()}/api/skills/{pack_id}/pack"
    if pack_id.startswith("role-"):
        url = f"{open_base()}/api/roles/{pack_id}/pack"
    tmp = WINMALE_HOME / "hub" / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    zip_path = tmp / f"{pack_id}.zip"
    eprint(f"download {url}")
    urllib.request.urlretrieve(url, zip_path)
    import zipfile

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(root)
    meta = root / pack_id / ".wm-skill-meta.json"
    meta.write_text(
        json.dumps(
            {
                "id": pack_id,
                "version": read_local_version(root, pack_id),
                "installed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"installed {pack_id} → {root / pack_id}")


def main() -> None:
    root = skills_root()
    p = argparse.ArgumentParser(prog="wm_hub.py", description="SkillHub pack lifecycle")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")
    sub.add_parser("doctor")
    sub.add_parser("cleanup")

    pe = sub.add_parser("enable")
    pe.add_argument("pack_id")
    pd = sub.add_parser("disable")
    pd.add_argument("pack_id")

    pr = sub.add_parser("rename")
    pr.add_argument("old_id")
    pr.add_argument("new_id")
    pr.add_argument("--no-alias", action="store_true")

    pu = sub.add_parser("update")
    pu.add_argument("pack_id", nargs="?")
    pu.add_argument("--hub-only", action="store_true")

    pi = sub.add_parser("install")
    pi.add_argument("pack_id")

    args = p.parse_args()
    if args.cmd == "list":
        cmd_list(root)
    elif args.cmd == "doctor":
        cmd_doctor(root)
    elif args.cmd == "cleanup":
        cmd_cleanup(root)
    elif args.cmd == "enable":
        cmd_enable(root, args.pack_id, True)
    elif args.cmd == "disable":
        cmd_enable(root, args.pack_id, False)
    elif args.cmd == "rename":
        cmd_rename(root, args.old_id, args.new_id, keep_alias=not args.no_alias)
    elif args.cmd == "update":
        cmd_update(root, args.pack_id, args.hub_only)
    elif args.cmd == "install":
        cmd_install(root, args.pack_id)
    else:
        p.error("unknown command")


if __name__ == "__main__":
    main()
