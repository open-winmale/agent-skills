#!/usr/bin/env python3
"""Shared SkillHub runtime helpers (auth, env, HTTP). Agent-facing CLIs import this."""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WINMALE_HOME = Path(os.environ.get("WINMALE_HOME") or Path.home() / ".winmale")
USER_ENV = Path(os.environ.get("WM_SKILLHUB_ENV") or WINMALE_HOME / "credentials.env")
CACHE_DIR = Path(os.environ.get("WM_TOKEN_CACHE_DIR") or WINMALE_HOME / "cache")
CACHE_FILE = Path(os.environ.get("WM_TOKEN_CACHE") or CACHE_DIR / "access_token.json")

_XS_REF_RE = re.compile(r"^@(xs|file|pack):(.+)$", re.DOTALL)
_XS_REQUIRE_RE = re.compile(
    r"""xs\.(?:require|run|call|capture|trace)\(\s*["']([^"']+)["']""",
    re.MULTILINE,
)

_WORKSPACE_SYNC_TOP = frozenset({"scripts", "skills", "projects", "tests", "tmp"})
_WORKSPACE_SKIP_PREFIXES = (
    "cn/",
    "hk/",
    "us/",
    "spots/",
    "projects/.revisions/",
    "projects/.published/",
)

_WORKSPACE_README = """# Agent 本地 Workspace（云镜像）

路径：本目录（默认 `~/.winmale/workspace`；`WM_WORKSPACE_HOME` 或兼容 `WM_XS_HOME` 可覆盖）。
与 `credentials.env` 同属用户态，**技能 pack 升级不会覆盖**。相对路径与云上用户 workspace 一致。

## 布局

```text
scripts/                 # 可复用库；裸名 xs.require("foo.xs") 对应 scripts/foo.xs
skills/
projects/
  analysis/{id}/
  backtest/{id}/         # selector.xs trading.xs …
  screener/{id}/
  reminders/{id}/
  watchlist/
tmp/
tests/
```

## 引用

| 前缀 | 含义 |
|------|------|
| `@xs:scripts/foo.xs` | 相对本目录（云相对路径） |
| `@xs:projects/backtest/demo/trading.xs` | 拨测阶段 |
| `@file:path.xs` | 绝对或相对 cwd |
| `@pack:wm-backtest/examples/xs/...` | 已装 skill pack |

兼容旧写法：`@xs:backtest/…` → `projects/backtest/…`；`@xs:analysis/…` → `projects/analysis/…`。

多文件 `xs.require`：本地试跑走 `xs-eval` 依赖闭包（`script_files` / `my/…`）；正式拨测须 `wm.sh workspace push` 同步到云。
"""


def eprint(*args: Any) -> None:
    print(*args, file=__import__("sys").stderr)


def workspace_home() -> Path:
    env = (os.environ.get("WM_WORKSPACE_HOME") or os.environ.get("WM_XS_HOME") or "").strip()
    if env:
        return Path(env).expanduser()
    return WINMALE_HOME / "workspace"


def xs_home() -> Path:
    """@xs: root — same as workspace_home (cloud-aligned mirror)."""
    return workspace_home()


def legacy_xs_home() -> Path:
    return WINMALE_HOME / "xs"


def _map_legacy_xs_rel(rel: str) -> str:
    """Map deprecated @xs:backtest|analysis paths onto projects/…."""
    rel = rel.replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    rel = rel.lstrip("/")
    if rel.startswith("projects/") or rel.startswith("scripts/") or rel.startswith("skills/"):
        return rel
    if rel.startswith("backtest/"):
        return "projects/" + rel
    if rel.startswith("analysis/"):
        return "projects/" + rel
    return rel


def ensure_workspace() -> Path:
    root = workspace_home()
    root.mkdir(parents=True, exist_ok=True)
    for sub in (
        "scripts",
        "skills",
        "projects",
        "projects/analysis",
        "projects/backtest",
        "projects/screener",
        "projects/reminders",
        "projects/watchlist",
        "tmp",
        "tests",
    ):
        (root / sub).mkdir(parents=True, exist_ok=True)
    readme = root / "README.md"
    if not readme.is_file():
        readme.write_text(_WORKSPACE_README, encoding="utf-8")
    _migrate_legacy_xs_tree(root)
    return root


def ensure_xs_workspace() -> Path:
    """Compat alias for ensure_workspace()."""
    return ensure_workspace()


def _migrate_legacy_xs_tree(workspace: Path) -> None:
    legacy = legacy_xs_home()
    if not legacy.is_dir() or legacy.resolve() == workspace.resolve():
        return
    marker = workspace / ".migrated_from_xs"
    if marker.is_file():
        return
    moved = 0
    for src in legacy.rglob("*"):
        if not src.is_file() or src.name == "README.md":
            continue
        try:
            rel = src.relative_to(legacy).as_posix()
        except ValueError:
            continue
        dest_rel = _map_legacy_xs_rel(rel)
        dest = workspace / dest_rel
        if dest.is_file():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        moved += 1
    marker.write_text(
        f"migrated_from={legacy}\nmoved_files={moved}\n",
        encoding="utf-8",
    )
    if moved:
        eprint(f"wm-workspace: migrated {moved} file(s) from {legacy} → {workspace}")


def resolve_skills_root(hub_scripts_dir: Path | None = None) -> Path:
    env = (os.environ.get("WM_SKILLS_ROOT") or "").strip()
    if env:
        return Path(env).expanduser()
    if hub_scripts_dir is not None:
        return skills_root_from_hub_scripts(hub_scripts_dir)
    # Prefer caller scripts dir; fallback to this file's pack layout.
    return skills_root_from_hub_scripts(Path(__file__).resolve().parent)


def _is_within(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def resolve_xs_ref(
    ref: str,
    *,
    cwd: Path | None = None,
    skills_root: Path | None = None,
) -> Path:
    """Resolve @xs: / @file: / @pack: to a filesystem path (does not read)."""
    m = _XS_REF_RE.match(ref.strip())
    if not m:
        raise ValueError(f"not an xs ref: {ref[:80]!r}")
    kind, raw = m.group(1), m.group(2).strip()
    if not raw:
        raise ValueError(f"empty path in xs ref: {ref[:80]!r}")
    if "\x00" in raw:
        raise ValueError("invalid path")
    cwd = cwd or Path.cwd()
    if kind == "xs":
        root = xs_home().resolve()
        rel = Path(_map_legacy_xs_rel(raw))
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"@xs: path must be relative without ..: {raw!r}")
        path = (root / rel).resolve()
        if not _is_within(root, path):
            raise ValueError(f"@xs: escapes xs home: {raw!r}")
        return path
    if kind == "file":
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = (cwd / path).resolve()
        else:
            path = path.resolve()
        return path
    # pack
    root = (skills_root or resolve_skills_root()).resolve()
    rel = Path(raw)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"@pack: path must be relative without ..: {raw!r}")
    path = (root / rel).resolve()
    if not _is_within(root, path):
        raise ValueError(f"@pack: escapes skills root: {raw!r}")
    return path


def expand_xs_ref_string(
    value: str,
    *,
    cwd: Path | None = None,
    skills_root: Path | None = None,
) -> str:
    if not isinstance(value, str) or not value.startswith("@"):
        return value
    if not _XS_REF_RE.match(value.strip()):
        return value
    path = resolve_xs_ref(value, cwd=cwd, skills_root=skills_root)
    if not path.is_file():
        raise FileNotFoundError(f"xs ref not found: {value} → {path}")
    return path.read_text(encoding="utf-8")


def expand_xs_refs(
    value: Any,
    *,
    cwd: Path | None = None,
    skills_root: Path | None = None,
) -> Any:
    """Recursively expand @xs:/@file:/@pack: string leaves to file contents."""
    cwd = cwd or Path.cwd()
    if isinstance(value, str):
        return expand_xs_ref_string(value, cwd=cwd, skills_root=skills_root)
    if isinstance(value, list):
        return [expand_xs_refs(v, cwd=cwd, skills_root=skills_root) for v in value]
    if isinstance(value, dict):
        return {
            k: expand_xs_refs(v, cwd=cwd, skills_root=skills_root)
            for k, v in value.items()
        }
    return value


def workspace_rel_for_path(path: Path, *, root: Path | None = None) -> str:
    root = (root or workspace_home()).resolve()
    path = path.resolve()
    if not _is_within(root, path):
        raise ValueError(f"path outside workspace: {path}")
    return path.relative_to(root).as_posix()


def my_overlay_key(rel: str) -> str:
    rel = rel.replace("\\", "/").lstrip("./")
    if rel.startswith("my/"):
        return rel
    return "my/" + rel


def collect_xs_deps(
    entry_path: Path,
    *,
    workspace: Path | None = None,
    max_files: int = 32,
    max_total_bytes: int = 2 << 20,
) -> dict[str, str]:
    """Static closure of xs.require|run|call|capture|trace("literal") under workspace.

    Returns script_files map keyed as my/<workspace-rel>.
    """
    workspace = (workspace or workspace_home()).resolve()
    entry_path = entry_path.resolve()
    if not entry_path.is_file():
        raise FileNotFoundError(str(entry_path))

    out: dict[str, str] = {}
    total = 0
    queue: list[Path] = [entry_path]
    seen: set[Path] = set()

    while queue:
        cur = queue.pop(0)
        if cur in seen:
            continue
        seen.add(cur)
        if not _is_within(workspace, cur):
            # Platform / pack paths are not packed into my overlay.
            continue
        text = cur.read_text(encoding="utf-8")
        rel = workspace_rel_for_path(cur, root=workspace)
        key = my_overlay_key(rel)
        if key not in out:
            if len(out) >= max_files:
                raise ValueError(
                    f"dependency closure exceeds {max_files} files; sync to cloud workspace instead"
                )
            total += len(text.encode("utf-8"))
            if total > max_total_bytes:
                raise ValueError(
                    f"dependency closure exceeds {max_total_bytes} bytes; sync to cloud workspace instead"
                )
            out[key] = text
        for dep in _XS_REQUIRE_RE.findall(text):
            dep = dep.strip().replace("\\", "/")
            if not dep or ".." in Path(dep).parts:
                continue
            # Platform built-ins: skip packing
            if dep.startswith(
                (
                    "sys/",
                    "xs/",
                    "assets/",
                    "web_echo/",
                    "help/",
                    "see/",
                    "input/",
                    "hover/",
                    "rags/",
                    "config/",
                    "tmp/",
                )
            ):
                continue
            if dep.startswith(("my/", "{my}/", "@my/")):
                if dep.startswith("{my}/"):
                    dep = dep[len("{my}/") :]
                elif dep.startswith("@my/"):
                    dep = dep[len("@my/") :]
                else:
                    dep = dep[len("my/") :]
            cand: Path | None = None
            if dep.startswith("scripts/") or dep.startswith("projects/") or dep.startswith("skills/"):
                cand = (workspace / dep).resolve()
            else:
                # Bare name → scripts/<name>; also try sibling of current file
                sibling = (cur.parent / dep).resolve()
                scripts = (workspace / "scripts" / dep).resolve()
                if sibling.is_file() and _is_within(workspace, sibling):
                    cand = sibling
                elif scripts.is_file():
                    cand = scripts
                else:
                    cand = scripts
            if cand is not None and cand.is_file() and cand not in seen:
                queue.append(cand)
    return out


def sync_path_allowed(rel: str) -> bool:
    rel = rel.replace("\\", "/").lstrip("./")
    if not rel or ".." in Path(rel).parts:
        return False
    top = rel.split("/", 1)[0]
    if top not in _WORKSPACE_SYNC_TOP:
        return False
    for pref in _WORKSPACE_SKIP_PREFIXES:
        if rel == pref.rstrip("/") or rel.startswith(pref):
            return False
    return True


def parse_project_rel(rel: str) -> tuple[str, str, str] | None:
    """projects/{kind}/{id}/{file...} → (kind, id, file)."""
    parts = rel.replace("\\", "/").strip("/").split("/")
    if len(parts) < 4 or parts[0] != "projects":
        return None
    kind, pid = parts[1], parts[2]
    if kind.startswith(".") or pid.startswith("."):
        return None
    file_rel = "/".join(parts[3:])
    if not file_rel or file_rel.startswith("."):
        return None
    return kind, pid, file_rel


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*([^#=]+)=(.*)\s*$", line)
        if not m:
            continue
        key = m.group(1).strip()
        val = m.group(2).strip().strip("\"'")
        os.environ.setdefault(key, val)


def migrate_legacy_env(skill_dir: Path | None = None) -> None:
    if USER_ENV.is_file():
        return
    if skill_dir is None:
        return
    legacy = skill_dir / ".env"
    if not legacy.is_file():
        return
    WINMALE_HOME.mkdir(parents=True, exist_ok=True)
    USER_ENV.write_text(legacy.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        USER_ENV.chmod(0o600)
    except OSError:
        pass
    eprint(f"wm-auth: migrated credentials {legacy} → {USER_ENV}")


def bootstrap_env(skill_dir: Path | None = None) -> None:
    migrate_legacy_env(skill_dir)
    load_env_file(USER_ENV)
    cursor = os.environ.get("CURSOR_PROJECT_DIR") or ""
    if cursor:
        load_env_file(Path(cursor) / ".env")
    load_env_file(Path.cwd() / ".env")
    if skill_dir is not None:
        load_env_file(skill_dir / ".env")


def api_base() -> str:
    return (os.environ.get("WINMALE_API_BASE") or "https://api.winmale.com").rstrip("/")


def client_creds() -> tuple[str, str]:
    cid = (os.environ.get("WINMALE_CLIENT_ID") or "").strip()
    secret = (
        os.environ.get("WINMALE_API_KEY")
        or os.environ.get("WINMALE_CLIENT_SECRET")
        or ""
    ).strip()
    return cid, secret


def _cache_valid(data: dict) -> str | None:
    tok = (data.get("access_token") or "").strip()
    exp = int(data.get("expires_at") or 0)
    if not tok or exp <= int(time.time()) + 120:
        return None
    return tok


def read_cache_token() -> str | None:
    if not CACHE_FILE.is_file():
        return None
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None
    return _cache_valid(data)


def read_cache_meta() -> tuple[bool, str]:
    if not CACHE_FILE.is_file():
        return False, ""
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return False, ""
    if not _cache_valid(data):
        return False, ""
    return True, str(data.get("expires_at_iso") or "")


def write_cache(token: str, expires_in: int) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    exp = now + max(60, int(expires_in or 7200))
    iso = datetime.fromtimestamp(exp, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "access_token": token,
        "expires_at": exp,
        "expires_at_iso": iso,
        "expires_in": max(60, int(expires_in or 7200)),
        "obtained_at": now,
        "scope": None,
        "token_type": "Bearer",
    }
    CACHE_FILE.write_text(json.dumps(payload), encoding="utf-8")


def http_post(
    url: str,
    body: str | bytes,
    content_type: str,
    token: str | None = None,
    timeout: int = 120,
) -> tuple[int, str]:
    return http_request(
        "POST",
        url,
        body=body,
        content_type=content_type,
        token=token,
        timeout=timeout,
    )


def http_request(
    method: str,
    url: str,
    *,
    body: str | bytes | None = None,
    content_type: str | None = None,
    token: str | None = None,
    user_token: str | None = None,
    timeout: int = 120,
) -> tuple[int, str]:
    data = None
    if body is not None:
        data = body if isinstance(body, bytes) else body.encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method.upper())
    if content_type:
        req.add_header("Content-Type", content_type)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if user_token:
        req.add_header("X-WM-User-Authorization", f"Bearer {user_token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        return e.code, raw


def get_access_token(*, force_refresh: bool = False, skill_dir: Path | None = None) -> str:
    bootstrap_env(skill_dir)
    if force_refresh or os.environ.get("WM_AUTH_FORCE_REFRESH") == "1":
        try:
            if CACHE_FILE.exists():
                CACHE_FILE.unlink()
        except OSError:
            pass

    tok = read_cache_token()
    if tok:
        ok, iso = read_cache_meta()
        if ok and os.environ.get("WM_AUTH_VERBOSE") == "1":
            eprint(f"wm-auth: cache hit expires_at={iso}")
        return tok

    cid, secret = client_creds()
    if not cid or not secret:
        eprint(
            "wm-auth: missing WINMALE_CLIENT_ID / WINMALE_API_KEY "
            f"(expected {USER_ENV} or env)"
        )
        raise SystemExit(2)

    form = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": cid,
            "client_secret": secret,
        }
    )
    status, raw = http_post(
        f"{api_base()}/v1/oauth/token",
        form,
        "application/x-www-form-urlencoded",
    )
    try:
        doc = json.loads(raw)
    except Exception:
        eprint(f"wm-auth: oauth failed HTTP {status}: {raw[:400]}")
        raise SystemExit(1)
    data = doc.get("data") if isinstance(doc.get("data"), dict) else {}
    token = (doc.get("access_token") or data.get("access_token") or "").strip()
    expires_in = int(doc.get("expires_in") or data.get("expires_in") or 7200)
    if not token:
        eprint(f"wm-auth: oauth failed: {raw[:400]}")
        raise SystemExit(1)
    write_cache(token, expires_in)
    _, iso = read_cache_meta()
    eprint(f"wm-auth: refreshed expires_at={iso}")
    return token


def is_auth_fail(resp_text: str, http_status: int | None = None) -> bool:
    if http_status == 401:
        return True
    try:
        d = json.loads(resp_text)
    except Exception:
        return "invalid_token" in resp_text.lower()
    blob = json.dumps(d, ensure_ascii=False).lower()
    code = str(d.get("code") or d.get("error") or "").upper()
    if "invalid_token" in blob or code in ("INVALID_TOKEN", "UNAUTHORIZED"):
        return True
    if str(d.get("http_status") or "") == "401" or d.get("status") == 401:
        return True
    return False


def post_json_authed(
    url: str,
    payload: dict,
    *,
    skill_dir: Path | None = None,
) -> tuple[int, str]:
    body = json.dumps(payload, ensure_ascii=False)
    token = get_access_token(skill_dir=skill_dir)
    status, raw = http_post(url, body, "application/json", token=token)
    if is_auth_fail(raw, status):
        eprint("wm-runtime: auth failed → force refresh once")
        token = get_access_token(force_refresh=True, skill_dir=skill_dir)
        status, raw = http_post(url, body, "application/json", token=token)
    if status >= 400 or "error" in raw.lower() and status != 200:
        log_telemetry_event(
            event_type="api_error" if status >= 400 else "business_error",
            skill_id=url.split("/")[-2] if "/skills/" in url else "wm-api",
            url=url,
            payload=payload,
            status=status,
            resp_text=raw,
        )
    return status, raw


def log_telemetry_event(
    event_type: str,
    skill_id: str,
    url: str,
    payload: dict,
    status: int,
    resp_text: str,
    error_msg: str = "",
) -> None:
    try:
        feedback_file = Path(
            os.environ.get("WM_FEEDBACK_EVENTS")
            or Path(os.environ.get("WINMALE_EVAL_ROOT") or Path(__file__).resolve().parents[3]) / "eval" / "feedback_events.jsonl"
        )
        if not feedback_file.parent.exists():
            feedback_file = WINMALE_HOME / "feedback_events.jsonl"
        feedback_file.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "session_id": os.environ.get("WM_SESSION_ID")
            or os.environ.get("CURSOR_SESSION_ID")
            or f"sess_{os.getpid()}_{int(time.time())}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "skill_id": skill_id,
            "url": url,
            "payload": payload,
            "http_status": status,
            "error_msg": error_msg or (resp_text[:300] if status >= 400 else ""),
            "raw_response": resp_text[:1000] if status >= 400 else "",
        }
        with feedback_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass


def print_result_or_full(raw: str, out_mode: str, *, result_key: str = "result") -> None:
    if out_mode != "result":
        print(raw if raw.endswith("\n") else raw + "\n", end="")
        return
    try:
        d = json.loads(raw)
    except Exception:
        print(raw)
        return
    data = d.get("data") if isinstance(d.get("data"), dict) else {}
    r = data.get(result_key, d.get(result_key, data if data else d))
    if isinstance(r, str):
        print(r)
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))


def skills_root_from_hub_scripts(scripts_dir: Path) -> Path:
    return scripts_dir.parent.parent


def pack_dir(skills_root: Path, pack_id: str) -> Path:
    return skills_root / pack_id
