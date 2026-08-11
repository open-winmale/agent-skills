#!/usr/bin/env python3
"""Publish local skills/ to SkillHub.cn without permanently rewriting SKILL.md.

Token sources (first hit wins):
  SKILLHUB_KEY / SKILLHUB_TOKEN env
  .env.skillhub.cn in repo root (gitignored)

Never prints the full API key.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
PLUGINS_DIR = ROOT / "plugins"
STATE_PATH = ROOT / "docs" / "SKILLHUB_CN_PUBLISH_STATE.json"
ENV_FILE = ROOT / ".env.skillhub.cn"
DEFAULT_HOST = "https://api.skillhub.cn"
FIRST_BATCH = [
    "wm-skillhub",
    "wm-company-card",
    "wm-company-business",
    "wm-valuation",
    "wm-notice-radar",
    "wm-dividend-quality",
    "wm-debt-safety",
    "wm-cashflow-quality",
    "wm-revenue-profit",
    "wm-discover",
    "wm-watchlist",
    "wm-reminder",
    "wm-screen-index",
    "wm-backtest",
]


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def mask_key(key: str) -> str:
    key = key.strip()
    if len(key) <= 8:
        return "skh_…****"
    return f"{key[:4]}…{key[-4:]}"


def load_dotenv_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def resolve_credentials() -> tuple[str, str]:
    env_file = load_dotenv_file(ENV_FILE)
    key = (
        os.environ.get("SKILLHUB_KEY")
        or os.environ.get("SKILLHUB_TOKEN")
        or env_file.get("SKILLHUB_KEY")
        or env_file.get("SKILLHUB_TOKEN")
        or ""
    ).strip()
    host = (
        os.environ.get("SKILLHUB_HOST")
        or env_file.get("SKILLHUB_HOST")
        or DEFAULT_HOST
    ).strip().rstrip("/")
    if not key:
        die(
            "missing SKILLHUB_KEY / SKILLHUB_TOKEN "
            f"(env or {ENV_FILE.name})"
        )
    if not key.startswith("skh_"):
        die("API key should start with skh_")
    return key, host


def find_skillhub_bin() -> str:
    path = shutil.which("skillhub")
    if path:
        return path
    home = Path.home() / ".local" / "bin" / "skillhub"
    if home.is_file() and os.access(home, os.X_OK):
        return str(home)
    die("skillhub CLI not found on PATH or ~/.local/bin/skillhub")


def run(cmd: list[str], *, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    # Redact key-like args in dry log
    shown = []
    skip_next = False
    for i, a in enumerate(cmd):
        if skip_next:
            skip_next = False
            shown.append("<redacted>")
            continue
        if a in ("--key", "--token") and i + 1 < len(cmd):
            shown.append(a)
            skip_next = True
            continue
        shown.append(a)
    print("+", " ".join(shown), flush=True)
    return subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        env=env,
        check=False if not check else False,
    )


def ensure_login(cli: str, key: str, host: str) -> None:
    env = os.environ.copy()
    # Prefer login --key
    cp = run([cli, "login", "--key", key, "--host", host], env=env, check=False)
    if cp.returncode == 0:
        if cp.stdout.strip():
            print(cp.stdout.strip())
        return
    # Fallback legacy
    cp2 = run(
        [cli, "auth", "login", "--token", key, "--host", host],
        env=env,
        check=False,
    )
    if cp2.returncode != 0:
        err = (cp.stderr or cp.stdout or "") + "\n" + (cp2.stderr or cp2.stdout or "")
        die(f"skillhub login failed:\n{err.strip()}")
    if cp2.stdout.strip():
        print(cp2.stdout.strip())


def api_get(host: str, path: str, key: str) -> Any:
    url = f"{host}{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "User-Agent": "agent-skills-publish-skillhub-cn/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        die(f"API GET {path} failed: HTTP {e.code}: {detail[:500]}")
    except Exception as e:  # noqa: BLE001
        die(f"API GET {path} failed: {e}")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    fm_raw, body = m.group(1), m.group(2)
    data: dict[str, Any] = {}
    # Minimal YAML-ish: key: value / key: "value"
    for line in fm_raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        data[k] = v
    return data, body


def dump_frontmatter(data: dict[str, Any]) -> str:
    # Stable preferred order for skillhub.cn
    order = [
        "slug",
        "displayName",
        "version",
        "name",
        "display_name",
        "description",
        "summary",
        "tags",
        "license",
        "homepage",
    ]
    keys = [k for k in order if k in data] + [k for k in data if k not in order]
    lines = ["---"]
    for k in keys:
        v = data[k]
        if isinstance(v, (list, dict)):
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        else:
            s = str(v)
            if any(c in s for c in (":", "#", "{", "}", "[", "]", "\n")) or s != s.strip():
                esc = s.replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'{k}: "{esc}"')
            else:
                # Prefer quoting Chinese / spaces
                if re.search(r"[\s\u4e00-\u9fff]", s) or not re.match(r"^[\w.\-+]+$", s):
                    esc = s.replace("\\", "\\\\").replace('"', '\\"')
                    lines.append(f'{k}: "{esc}"')
                else:
                    lines.append(f"{k}: {s}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def parse_semver(v: str) -> tuple[int, int, int]:
    v = (v or "").strip().lstrip("v")
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", v)
    if not m:
        return (0, 0, 0)
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def semver_cmp(a: str, b: str) -> int:
    aa, bb = parse_semver(a), parse_semver(b)
    return (aa > bb) - (aa < bb)


def discover_skill_dirs() -> list[Path]:
    """Prefer top-level skills/ over plugins/**/skills duplicates (same slug)."""
    by_slug: dict[str, Path] = {}

    def consider(p: Path, *, preferred: bool) -> None:
        if not (p.is_dir() and (p / "SKILL.md").is_file()):
            return
        text = (p / "SKILL.md").read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(text)
        slug = str(fm.get("slug") or fm.get("name") or p.name).strip()
        if not slug:
            return
        if slug not in by_slug or preferred:
            by_slug[slug] = p

    if SKILLS_DIR.is_dir():
        for p in sorted(SKILLS_DIR.iterdir()):
            consider(p, preferred=True)
    if PLUGINS_DIR.is_dir():
        for skill_md in sorted(PLUGINS_DIR.glob("**/skills/*/SKILL.md")):
            consider(skill_md.parent, preferred=False)
    return [by_slug[k] for k in sorted(by_slug)]


def normalize_meta(fm: dict[str, Any], dirname: str) -> dict[str, Any]:
    slug = str(fm.get("slug") or fm.get("name") or dirname).strip()
    display = str(
        fm.get("displayName") or fm.get("display_name") or fm.get("name") or slug
    ).strip()
    version = str(fm.get("version") or "0.0.0").strip()
    desc = str(fm.get("description") or "").strip()
    summary = str(fm.get("summary") or "").strip()
    if not summary and desc:
        summary = desc.split("。")[0][:120]
    out = dict(fm)
    out["slug"] = slug
    out["displayName"] = display
    out["version"] = version
    if desc:
        out["description"] = desc
    if summary:
        out["summary"] = summary
    # keep Cursor fields
    if "name" not in out:
        out["name"] = slug
    if "display_name" not in out:
        out["display_name"] = display
    return out


# SkillHub.cn rejects some extensions (e.g. .xs). Keep originals in git; strip in staging.
STAGING_SKIP_GLOBS = (
    ".env",
    ".env.*",
    ".wm-skill-meta.json",
    "__pycache__",
    "*.pyc",
    ".DS_Store",
    ".git",
    "*.xs",  # not in SkillHub.cn allowed file types
)


def stage_skill(src: Path, meta: dict[str, Any], body: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix=f"skillhub-cn-{meta['slug']}-"))
    ignore = shutil.ignore_patterns(*STAGING_SKIP_GLOBS)
    shutil.copytree(src, tmp / src.name, ignore=ignore)
    staged = tmp / src.name
    (staged / "SKILL.md").write_text(dump_frontmatter(meta) + body, encoding="utf-8")
    return staged


def extract_remote_skills(payload: Any) -> list[dict[str, Any]]:
    # Tolerate various shapes (SkillHub.cn dashboard returns {"skills":[...]})
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        data = payload.get("data", payload)
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = (
                data.get("skills")
                or data.get("items")
                or data.get("list")
                or data.get("records")
                or []
            )
            if not items and payload.get("skills"):
                items = payload.get("skills") or []
        else:
            items = []
    else:
        items = []
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        ns = it.get("namespace") if isinstance(it.get("namespace"), dict) else {}
        slug = str(
            it.get("slug")
            or ns.get("publicSlug")
            or ""
        ).strip()
        # Dashboard "name" is the Chinese display title on SkillHub.cn
        display = str(
            it.get("displayName")
            or it.get("display_name")
            or it.get("name")
            or it.get("title")
            or ""
        ).strip()
        version = str(
            it.get("version")
            or it.get("latestApprovedVersion")
            or it.get("latestVersion")
            or ""
        ).strip()
        url = str(
            it.get("url")
            or it.get("pageUrl")
            or it.get("homepage")
            or it.get("skillUrl")
            or ""
        ).strip()
        if not url and slug:
            handle = str((ns or {}).get("handle") or "").strip()
            if handle:
                url = f"https://skillhub.cn/s/{handle}/{slug}"
            else:
                url = f"https://skillhub.cn/skills/{slug}"
        out.append(
            {
                "slug": slug,
                "displayName": display,
                "version": version,
                "url": url,
                "raw": it,
            }
        )
    return out


def load_state() -> dict[str, Any]:
    if STATE_PATH.is_file():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"skills": {}}
    return {"skills": {}}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def git_sha() -> str:
    try:
        cp = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
            text=True,
            capture_output=True,
            check=True,
        )
        return cp.stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def decide_action(
    meta: dict[str, Any],
    by_slug: dict[str, dict[str, Any]],
    by_display: dict[str, dict[str, Any]],
    *,
    force: bool,
) -> tuple[str, str]:
    """Return (status, reason). status: publish|skip"""
    slug = meta["slug"]
    display = meta["displayName"]
    local_v = meta["version"]

    remote = by_slug.get(slug)
    if remote:
        rv = remote.get("version") or "0.0.0"
        cmp = semver_cmp(rv, local_v)
        if cmp > 0:
            return "skip", f"remote {rv} > local {local_v}"
        if cmp == 0 and not force:
            return "skip", f"same version {local_v}"
        if cmp < 0:
            return "publish", f"upgrade {rv} → {local_v}"
        return "publish", "force republish"

    # displayName exact match against existing (Chinese dashboard skills etc.)
    dmatch = by_display.get(display)
    if dmatch and dmatch.get("slug") != slug:
        rv = dmatch.get("version") or "0.0.0"
        if semver_cmp(rv, local_v) >= 0 and not force:
            return "skip", (
                f"displayName '{display}' already published "
                f"as slug={dmatch.get('slug')} v{rv}"
            )

    return "publish", "new"


def publish_one(
    cli: str,
    staged: Path,
    host: str,
    key: str,
    changelog: str,
    *,
    dry_run: bool,
    retries: int = 6,
) -> tuple[bool, str, str]:
    cmd = [
        cli,
        "publish",
        str(staged),
        "--host",
        host,
        "--changelog",
        changelog,
        "--json",
        "--token",
        key,
    ]
    if dry_run:
        cmd.append("--dry-run")

    attempt = 0
    out = err = ""
    while True:
        attempt += 1
        cp = run(cmd, check=False)
        out = (cp.stdout or "").strip()
        err = (cp.stderr or "").strip()
        combined = "\n".join([out, err]).strip()
        rate_limited = (
            "RATE_LIMITED" in combined
            or "请求过于频繁" in combined
            or "发布频率过高" in combined
            or '"status": 429' in combined
            or '"status":429' in combined
        )
        if rate_limited and attempt < retries and not dry_run:
            wait = min(90, 10 * attempt)
            print(f"rate-limited; sleep {wait}s then retry ({attempt}/{retries})", flush=True)
            time.sleep(wait)
            continue
        break

    url = ""
    ok = False
    if out:
        try:
            payload = json.loads(out)
            if isinstance(payload, dict):
                data = payload.get("data", payload) if "data" in payload else payload
                if isinstance(data, dict):
                    url = str(
                        data.get("url")
                        or data.get("pageUrl")
                        or data.get("skillUrl")
                        or ""
                    )
                    slug = data.get("slug")
                    if not url and slug:
                        url = f"https://skillhub.cn/skills/{slug}"
                    ok = bool(
                        data.get("ok") is True
                        or data.get("success") is True
                        or data.get("dryRun") is True
                        or (data.get("slug") and data.get("version") and data.get("success") is not False)
                    )
                    if data.get("success") is False or data.get("ok") is False:
                        ok = False
        except json.JSONDecodeError:
            m = re.search(r"https?://\S+", out)
            if m:
                url = m.group(0).rstrip(".,)")
            ok = cp.returncode == 0
        print(out)
    else:
        ok = cp.returncode == 0
    if err:
        print(err, file=sys.stderr)
    if cp.returncode != 0:
        ok = False
    return ok, url, err or out


def main() -> None:
    ap = argparse.ArgumentParser(description="Publish skills to SkillHub.cn")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="", help="comma-separated slugs")
    ap.add_argument(
        "--force",
        action="store_true",
        help="publish even when remote version == local",
    )
    ap.add_argument("--list", action="store_true", help="list local vs remote only")
    ap.add_argument(
        "--batch",
        default="first",
        choices=["first", "all"],
        help="default first-batch wm-* set; 'all' = every local skill",
    )
    args = ap.parse_args()

    key, host = resolve_credentials()
    print(f"host={host}")
    print(f"key={mask_key(key)}")

    cli = find_skillhub_bin()
    print(f"cli={cli}")

    ensure_login(cli, key, host)

    me = api_get(host, "/api/v1/auth/me", key)
    me_name = ""
    if isinstance(me, dict):
        data = me.get("data", me)
        if isinstance(data, dict):
            me_name = str(data.get("name") or data.get("username") or data.get("email") or "")
    if me_name:
        print(f"auth.me={me_name}")

    dash = api_get(host, "/api/v1/dashboard/skills?page=1&pageSize=100", key)
    remote_skills = extract_remote_skills(dash)
    by_slug = {r["slug"]: r for r in remote_skills if r.get("slug")}
    by_display = {r["displayName"]: r for r in remote_skills if r.get("displayName")}
    print(f"remote_dashboard_skills={len(remote_skills)}")

    only = {s.strip() for s in args.only.split(",") if s.strip()}
    skill_dirs = discover_skill_dirs()
    rows: list[dict[str, Any]] = []

    for src in skill_dirs:
        text = (src / "SKILL.md").read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        meta = normalize_meta(fm, src.name)
        slug = meta["slug"]
        if only and slug not in only:
            continue
        if args.batch == "first" and not only and slug not in FIRST_BATCH:
            continue
        status, reason = decide_action(meta, by_slug, by_display, force=args.force)
        remote = by_slug.get(slug) or by_display.get(meta["displayName"])
        rows.append(
            {
                "slug": slug,
                "displayName": meta["displayName"],
                "version": meta["version"],
                "path": str(src.relative_to(ROOT)),
                "status": status,
                "reason": reason,
                "remote_slug": (remote or {}).get("slug", ""),
                "remote_version": (remote or {}).get("version", ""),
                "remote_url": (remote or {}).get("url", ""),
                "in_first_batch": slug in FIRST_BATCH,
                "src": src,
                "meta": meta,
                "body": body,
            }
        )

    # Pretty table
    print()
    print(f"{'slug':<24} {'local':<10} {'remote':<10} {'action':<10} reason")
    print("-" * 90)
    for r in rows:
        if args.batch == "first" and not only and not r["in_first_batch"] and args.list:
            # show all when listing without --only
            pass
        print(
            f"{r['slug']:<24} {r['version']:<10} {r['remote_version'] or '-':<10} "
            f"{r['status']:<10} {r['reason']}"
        )

    if args.list:
        return

    # Filter to actionable set
    targets = []
    for r in rows:
        if only:
            targets.append(r)
        elif args.batch == "first":
            if r["in_first_batch"]:
                targets.append(r)
        else:
            targets.append(r)

    sha = git_sha()
    changelog = f"sync from JerryZhou/agent-skills@{sha}"
    state = load_state()
    state.setdefault("skills", {})
    failures = 0
    results = []

    for r in targets:
        slug = r["slug"]
        if r["status"] == "skip":
            results.append(
                {
                    "slug": slug,
                    "version": r["version"],
                    "status": "skipped",
                    "url": r["remote_url"] or f"https://skillhub.cn/skills/{slug}",
                    "reason": r["reason"],
                }
            )
            continue

        staged_root = None
        try:
            # Pace publishes to avoid SkillHub.cn RATE_LIMITED (429).
            time.sleep(8)
            staged = stage_skill(r["src"], r["meta"], r["body"])
            staged_root = staged.parent
            ok, url, detail = publish_one(
                cli,
                staged,
                host,
                key,
                changelog,
                dry_run=args.dry_run,
            )
            if not url:
                url = f"https://skillhub.cn/skills/{slug}"
            if ok:
                status = "dry-run" if args.dry_run else "published"
                results.append(
                    {
                        "slug": slug,
                        "version": r["version"],
                        "status": status,
                        "url": url,
                        "reason": r["reason"],
                    }
                )
                if not args.dry_run:
                    state["skills"][slug] = {
                        "version": r["version"],
                        "displayName": r["displayName"],
                        "url": url,
                        "published_at": datetime.now(timezone.utc).strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        ),
                        "git_sha": sha,
                    }
            else:
                failures += 1
                results.append(
                    {
                        "slug": slug,
                        "version": r["version"],
                        "status": "failed",
                        "url": url,
                        "reason": detail[:300],
                    }
                )
        finally:
            if staged_root and staged_root.exists():
                shutil.rmtree(staged_root, ignore_errors=True)

    if not args.dry_run:
        save_state(state)

    print()
    print("== results ==")
    print(f"{'slug':<24} {'version':<10} {'status':<10} url")
    for x in results:
        print(f"{x['slug']:<24} {x['version']:<10} {x['status']:<10} {x['url']}")

    if failures:
        die(f"{failures} publish failure(s)", 2)


if __name__ == "__main__":
    main()
