#!/usr/bin/env python3
"""wm_workspace.py — local cloud-aligned workspace: init|path|pull|push."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _wm_runtime import (  # noqa: E402
    api_base,
    eprint,
    ensure_workspace,
    get_access_token,
    http_request,
    parse_project_rel,
    post_json_authed,
    sync_path_allowed,
    workspace_home,
    workspace_rel_for_path,
)


def _user_token() -> str:
    return (
        os.environ.get("WINMALE_USER_TOKEN")
        or os.environ.get("WM_USER_TOKEN")
        or ""
    ).strip()


def _unwrap(raw: str) -> dict:
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SystemExit(f"bad JSON response: {e}: {raw[:300]}") from e
    if isinstance(doc.get("data"), dict):
        return doc["data"]
    return doc if isinstance(doc, dict) else {}


def _xs_call(xs: str, args: dict, *, skill_dir: Path) -> dict:
    url = f"{api_base()}/v1/analysis/xs/eval"
    payload = {
        "symbol": "600519",
        "mode": "call",
        "xs": xs,
        "args": args,
    }
    status, raw = post_json_authed(url, payload, skill_dir=skill_dir)
    data = _unwrap(raw)
    if status >= 400 or data.get("error") or (
        isinstance(data.get("ok"), bool) and not data.get("ok")
    ):
        # OpenAPI envelope may put error at top-level of raw
        try:
            top = json.loads(raw)
        except Exception:
            top = {}
        err = top.get("error") or data.get("error") or raw[:400]
        raise SystemExit(f"xs/eval failed HTTP {status}: {err}")
    result = data.get("result", data)
    if isinstance(result, dict):
        return result
    return {"result": result}


def _http_list(path: str, *, skill_dir: Path) -> list[dict]:
    ut = _user_token()
    if not ut:
        # App-token path via workspace.list
        out = _xs_call(
            'return workspace.list(DEFAULT(path, ""))',
            {"path": path},
            skill_dir=skill_dir,
        )
        entries = out.get("entries") or out.get("result") or out
        if isinstance(entries, dict):
            entries = entries.get("entries") or []
        if not isinstance(entries, list):
            raise SystemExit(f"unexpected list shape: {out!r}")
        return [e for e in entries if isinstance(e, dict)]
    q = urllib.parse.urlencode({"path": path, "limit": "500"})
    token = get_access_token(skill_dir=skill_dir)
    status, raw = http_request(
        "GET",
        f"{api_base()}/v1/workspace?{q}",
        token=token,
        user_token=ut,
    )
    data = _unwrap(raw)
    if status >= 400:
        raise SystemExit(f"list failed HTTP {status}: {raw[:300]}")
    return list(data.get("entries") or [])


def _http_read(path: str, *, skill_dir: Path) -> str:
    ut = _user_token()
    if not ut:
        out = _xs_call(
            "return workspace.read(path)",
            {"path": path},
            skill_dir=skill_dir,
        )
        if isinstance(out.get("content"), str):
            return out["content"]
        if isinstance(out.get("result"), str):
            return out["result"]
        raise SystemExit(f"unexpected read shape: {out!r}")
    q = urllib.parse.urlencode({"path": path})
    token = get_access_token(skill_dir=skill_dir)
    status, raw = http_request(
        "GET",
        f"{api_base()}/v1/workspace/file?{q}",
        token=token,
        user_token=ut,
    )
    data = _unwrap(raw)
    if status >= 400:
        raise SystemExit(f"read failed HTTP {status}: {raw[:300]}")
    return str(data.get("content") or "")


def _http_write(path: str, content: str, *, skill_dir: Path) -> None:
    ut = _user_token()
    proj = parse_project_rel(path)
    if proj:
        kind, pid, file_rel = proj
        # Prefer project CAS write via XS host
        _xs_call(
            "return workspace.project_write(kind, id, file, content, MAP{})",
            {"kind": kind, "id": pid, "file": file_rel, "content": content},
            skill_dir=skill_dir,
        )
        return
    if not ut:
        # Request args bind as bare idents (path/content), not ARGS.* (ARGS is a vfunc).
        _xs_call(
            "return workspace.write(path, content)",
            {"path": path, "content": content},
            skill_dir=skill_dir,
        )
        return
    token = get_access_token(skill_dir=skill_dir)
    status, raw = http_request(
        "PUT",
        f"{api_base()}/v1/workspace/file",
        body=json.dumps({"path": path, "content": content}, ensure_ascii=False),
        content_type="application/json",
        token=token,
        user_token=ut,
    )
    if status >= 400:
        raise SystemExit(f"write failed HTTP {status}: {raw[:300]}")


def _iter_local_files(root: Path, rel: str) -> list[tuple[str, Path]]:
    base = root / rel if rel else root
    if base.is_file():
        r = workspace_rel_for_path(base, root=root)
        return [(r, base)] if sync_path_allowed(r) else []
    out: list[tuple[str, Path]] = []
    if not base.is_dir():
        return out
    for p in sorted(base.rglob("*")):
        if not p.is_file() or p.name == "README.md" or p.name.startswith("."):
            continue
        r = workspace_rel_for_path(p, root=root)
        if sync_path_allowed(r):
            out.append((r, p))
    return out


def _collect_remote_files(path: str, *, skill_dir: Path) -> list[str]:
    """Recursively list remote file paths under path."""
    files: list[str] = []
    stack = [path]
    while stack:
        cur = stack.pop()
        for e in _http_list(cur, skill_dir=skill_dir):
            name = str(e.get("name") or "")
            ep = str(e.get("path") or "").replace("\\", "/")
            if not ep:
                ep = f"{cur.rstrip('/')}/{name}" if cur else name
            if e.get("is_dir"):
                if sync_path_allowed(ep + "/") or sync_path_allowed(ep):
                    stack.append(ep)
            else:
                if sync_path_allowed(ep):
                    files.append(ep)
    return files


def cmd_push(rel: str, *, skill_dir: Path) -> None:
    root = ensure_workspace()
    items = _iter_local_files(root, rel)
    if not items:
        eprint(f"nothing to push under {rel or '.'}")
        return
    for r, p in items:
        content = p.read_text(encoding="utf-8")
        eprint(f"push {r} ({len(content)} bytes)")
        _http_write(r, content, skill_dir=skill_dir)
    print(json.dumps({"pushed": len(items), "root": str(root)}, ensure_ascii=False))


def cmd_pull(rel: str, *, skill_dir: Path) -> None:
    root = ensure_workspace()
    remote_root = rel.strip("/") if rel else ""
    files = _collect_remote_files(remote_root, skill_dir=skill_dir)
    if not files and remote_root:
        # single file?
        try:
            content = _http_read(remote_root, skill_dir=skill_dir)
            files = [remote_root]
            dest = root / remote_root
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            print(json.dumps({"pulled": 1, "root": str(root)}, ensure_ascii=False))
            return
        except SystemExit:
            raise
    n = 0
    for fp in files:
        content = _http_read(fp, skill_dir=skill_dir)
        dest = root / fp
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        eprint(f"pull {fp} ({len(content)} bytes)")
        n += 1
    print(json.dumps({"pulled": n, "root": str(root)}, ensure_ascii=False))


def main() -> None:
    p = argparse.ArgumentParser(description="Local↔cloud workspace mirror")
    p.add_argument(
        "action",
        choices=("init", "path", "pull", "push"),
        help="init|path|pull|push",
    )
    p.add_argument(
        "path",
        nargs="?",
        default="",
        help="relative workspace path for pull/push (optional)",
    )
    ns = p.parse_args()
    skill_dir = Path(__file__).resolve().parent.parent
    if ns.action == "path":
        print(workspace_home())
        return
    if ns.action == "init":
        print(ensure_workspace())
        return
    if ns.action == "push":
        cmd_push(ns.path, skill_dir=skill_dir)
        return
    cmd_pull(ns.path, skill_dir=skill_dir)


if __name__ == "__main__":
    main()
