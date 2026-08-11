#!/usr/bin/env bash
# SkillHub full sync: install missing catalog packs + upgrade outdated ones.
# Credentials live in ~/.winmale/ (never inside skill packs).
#
# Usage:
#   bash scripts/update-from-catalog.sh              # full management (default)
#   bash scripts/update-from-catalog.sh --all         # same as default
#   bash scripts/update-from-catalog.sh --installed-only   # only upgrade already-installed
#   bash scripts/update-from-catalog.sh --hub-only
#   bash scripts/update-from-catalog.sh --check | --dry-run   # preview only (no download)
#   bash scripts/update-from-catalog.sh wm-xs         # install/update one id
set -euo pipefail

OPEN_BASE="${WINMALE_OPEN_BASE:-https://open.winmale.com}"
OPEN_BASE="${OPEN_BASE%/}"
CATALOG_URL="${SKILLHUB_CATALOG_URL:-$OPEN_BASE/api/skills}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_ROOT="$(cd "$HUB_DIR/.." && pwd)"
WINMALE_HOME="${WINMALE_HOME:-$HOME/.winmale}"
USER_ENV="${WM_SKILLHUB_ENV:-$WINMALE_HOME/credentials.env}"
LEGACY_ENV="$HUB_DIR/.env"
BACKUP_ROOT="${WM_SKILLHUB_BACKUP_ROOT:-$WINMALE_HOME/backups/skills}"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/wm-skillhub-update.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

only_id=""
hub_only=false
installed_only=false
dry_run=false
mode="full"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hub-only) hub_only=true; only_id="wm-skillhub"; shift ;;
    --installed-only) installed_only=true; mode="installed"; shift ;;
    --all|--full) mode="full"; shift ;;
    --check|--dry-run) dry_run=true; shift ;;
    -h|--help)
      cat <<'EOF'
SkillHub full sync: install missing catalog packs + upgrade outdated ones.
Credentials live in ~/.winmale/ (never inside skill packs).

Usage:
  bash scripts/update-from-catalog.sh              # full management (default)
  bash scripts/update-from-catalog.sh --all         # same as default
  bash scripts/update-from-catalog.sh --installed-only   # only upgrade already-installed
  bash scripts/update-from-catalog.sh --hub-only
  bash scripts/update-from-catalog.sh --check | --dry-run   # preview only (no download)
  bash scripts/update-from-catalog.sh wm-xs         # install/update one id
EOF
      exit 0
      ;;
    -*)
      echo "unknown flag: $1" >&2
      exit 1
      ;;
    *)
      only_id="$1"
      shift
      ;;
  esac
done

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing required command: $1" >&2
    exit 1
  }
}

need_cmd curl
need_cmd unzip
need_cmd python3

echo "catalog: $CATALOG_URL"
echo "skills root: $SKILLS_ROOT"
echo "mode: $mode$([ -n "$only_id" ] && echo " (only=$only_id)" || true)$([ "$dry_run" = true ] && echo " [dry-run]" || true)"

# Migrate legacy skill-dir .env once (upgrades must not depend on pack-local secrets).
if [[ ! -f "$USER_ENV" && -f "$LEGACY_ENV" ]]; then
  mkdir -p "$WINMALE_HOME"
  cp "$LEGACY_ENV" "$USER_ENV"
  chmod 600 "$USER_ENV" 2>/dev/null || true
  echo "migrated credentials $LEGACY_ENV → $USER_ENV"
fi

curl -fsSL "$CATALOG_URL" -o "$TMP_DIR/catalog.json"

python3 - "$TMP_DIR/catalog.json" "$SKILLS_ROOT" "$TMP_DIR" "$only_id" "$hub_only" "$OPEN_BASE" "$installed_only" "$dry_run" "$BACKUP_ROOT" <<'PY'
import json, os, shutil, subprocess, sys, urllib.request
from pathlib import Path

(
    cat_path,
    skills_root,
    tmp,
    only_id,
    hub_only,
    open_base,
    installed_only,
    dry_run,
    backup_root,
) = sys.argv[1:10]
hub_only = hub_only == "true"
installed_only = installed_only == "true"
dry_run = dry_run == "true"
open_base = (open_base or "https://open.winmale.com").rstrip("/")
raw = json.loads(Path(cat_path).read_text(encoding="utf-8"))
# Open API wraps catalog as {data:{skills,roles,hub_version,...}, meta:{...}}.
doc = raw.get("data") if isinstance(raw, dict) and isinstance(raw.get("data"), dict) and (
    "skills" in raw["data"] or "roles" in raw["data"]
) else raw
if not isinstance(doc, dict):
    raise SystemExit(f"catalog shape unexpected: {type(doc).__name__}")
entries = list(doc.get("skills") or []) + list(doc.get("roles") or [])
hub_ver = str(doc.get("hub_version") or "").strip()
if hub_ver:
    print(f"hub_version (remote): {hub_ver}")

# Old id → new id (local rename stubs / catalog replacements).
ALIASES = {
    "wm-xs-eval-guide": "wm-xs",
    "wm-quote-snapshot": "wm-company-card",
    "wm-screener-mine": "wm-screen-index",
    "wm-cashflow": "wm-cashflow-quality",
    "wm-debt": "wm-debt-safety",
}

SKIP_VIS = frozenset({"deprecated", "hidden", "internal", "partner"})

def local_ver(entry_id: str) -> str:
    meta = Path(skills_root) / entry_id / ".wm-skill-meta.json"
    man = Path(skills_root) / entry_id / "manifest.json"
    skill = Path(skills_root) / entry_id / "SKILL.md"
    if meta.is_file():
        try:
            return str(json.loads(meta.read_text(encoding="utf-8")).get("version") or "")
        except Exception:
            pass
    if man.is_file():
        try:
            return str(json.loads(man.read_text(encoding="utf-8")).get("version") or "")
        except Exception:
            pass
    if skill.is_file():
        for line in skill.read_text(encoding="utf-8").splitlines()[:20]:
            if line.startswith("version:"):
                return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""

def semver_tuple(v: str):
    parts = []
    for p in (v or "0").split("."):
        try:
            parts.append(int("".join(ch for ch in p if ch.isdigit()) or "0"))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])

def outdated(local: str, remote: str) -> bool:
    if not remote:
        return False
    if not local:
        return True
    return semver_tuple(local) < semver_tuple(remote)

def pack_url_for(e: dict) -> str:
    eid = str(e.get("id") or "").strip()
    url = (e.get("pack_url") or e.get("pack_version_url") or "").strip()
    if url:
        return url
    if eid == "wm-skillhub":
        url = (doc.get("hub_pack_url") or doc.get("hub_pack_version_url") or "").strip()
        if url:
            return url
    kind = "roles" if (
        str(e.get("kind") or "").lower() == "role" or eid.startswith("role-")
    ) else "skills"
    return f"{open_base}/api/{kind}/{eid}/pack"

def is_installed(eid: str) -> bool:
    return (Path(skills_root) / eid).is_dir() and (Path(skills_root) / eid / "SKILL.md").is_file()

def changelog_of(e: dict) -> str:
    cl = e.get("changelog")
    if isinstance(cl, list):
        return " | ".join(str(x).strip() for x in cl if str(x).strip())
    return str(cl or "").strip()

by_id = {}
for e in entries:
    eid = str(e.get("id") or "").strip()
    if eid:
        by_id[eid] = e

# Orphan / deprecated local packs: always surface migration notes.
for old, new in ALIASES.items():
    if is_installed(old):
        lv = local_ver(old)
        print(f"note: local deprecated/orphan {old} (v{lv or '?'}) → use {new}")
        if new in by_id and not is_installed(new):
            print(f"note: will install replacement {new}")
        elif new in by_id and is_installed(new):
            print(f"note: replacement {new} already installed (v{local_ver(new) or '?'})")

force_ids = set()
for old, new in ALIASES.items():
    if is_installed(old) and new in by_id and not is_installed(new):
        force_ids.add(new)

targets = []
seen = set()
for e in entries:
    eid = str(e.get("id") or "").strip()
    if not eid or eid in seen:
        continue
    vis = str(e.get("visibility") or "public").strip().lower()
    if vis in SKIP_VIS:
        # Still honor replaced_by when local still has the deprecated id.
        repl = str(e.get("replaced_by") or ALIASES.get(eid) or "").strip()
        if repl and is_installed(eid) and repl in by_id and not is_installed(repl):
            print(f"note: {eid} deprecated → install replaced_by {repl}")
            force_ids.add(repl)
            e = by_id[repl]
            eid = repl
            vis = str(e.get("visibility") or "public").strip().lower()
            if vis in SKIP_VIS:
                continue
        else:
            continue
    if only_id and eid != only_id:
        continue
    if hub_only and eid != "wm-skillhub":
        continue

    installed = is_installed(eid)
    remote = str(e.get("version") or "").strip()
    local = local_ver(eid)

    if installed_only and not installed and eid != "wm-skillhub" and eid not in force_ids:
        continue
    if not installed or outdated(local, remote) or (eid == "wm-skillhub" and only_id == "wm-skillhub"):
        targets.append((e, "install" if not installed else "update", local, remote))
        seen.add(eid)

if not targets:
    print("nothing to update (local versions current; no missing packs)")
    sys.exit(0)

print(f"plan: {len(targets)} pack(s)")
for e, action, local, remote in targets:
    eid = e["id"]
    cl = changelog_of(e)
    line = f"  {action} {eid}: {local or '—'} → {remote or e.get('version')}"
    if cl:
        line += f"\n    changelog: {cl}"
    print(line)

if dry_run:
    print("dry-run: no download / no unzip")
    sys.exit(0)

def backup_pack(eid: str) -> str:
    src = Path(skills_root) / eid
    if not src.is_dir():
        return ""
    from datetime import datetime, timezone
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = Path(backup_root) / eid / stamp
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".env", ".wm-skill-meta.json"))
    # keep last 3 backups
    versions = sorted((Path(backup_root) / eid).glob("*"), reverse=True)
    for old in versions[3:]:
        if old.is_dir():
            shutil.rmtree(old, ignore_errors=True)
    return str(dest)

# Install hub last when present (self-update safety: others first, then hub).
targets_sorted = sorted(
    targets,
    key=lambda t: (1 if t[0].get("id") == "wm-skillhub" else 0, t[0].get("id") or ""),
)

for e, action, local, remote in targets_sorted:
    eid = e["id"]
    url = pack_url_for(e)
    if not url:
        print(f"skip {eid}: no pack_url and no API fallback", file=sys.stderr)
        continue
    zip_path = Path(tmp) / f"{eid}.zip"
    stage = Path(tmp) / f"stage-{eid}"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)
    cl = changelog_of(e)
    print(f"{action} {eid}: {local or '—'} → {remote or e.get('version')} via {url}")
    if cl:
        print(f"  changelog: {cl}")
    urllib.request.urlretrieve(url, zip_path)
    # Stage unzip first: reject bad packs before touching the live skills tree.
    subprocess.check_call(["unzip", "-oq", str(zip_path), "-d", str(stage)])
    staged = stage / eid
    if not (staged / "SKILL.md").is_file():
        raise SystemExit(f"acceptance failed: {eid} SKILL.md missing in pack staging")
    bak = ""
    if action == "update" and is_installed(eid):
        bak = backup_pack(eid)
        if bak:
            print(f"  backup: {bak}")
    # Live apply (zip layout is skills/{id}/...); secrets (.env) are not in official packs.
    subprocess.check_call(["unzip", "-oq", str(zip_path), "-d", skills_root])

    meta = {
        "id": eid,
        "version": e.get("version"),
        "installed_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if cl:
        meta["changelog"] = cl
    if bak:
        meta["previous_backup"] = bak
    if str(e.get("kind") or "").lower() == "role" or eid.startswith("role-"):
        meta["kind"] = "role"
    meta_path = Path(skills_root) / eid / ".wm-skill-meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    skill = Path(skills_root) / eid / "SKILL.md"
    sidecar = Path(skills_root) / eid / "_skillhub_meta.json"
    if not skill.is_file() or not skill.read_text(encoding="utf-8").startswith("---"):
        raise SystemExit(f"acceptance failed: {eid} SKILL.md frontmatter missing")
    if not sidecar.is_file():
        raise SystemExit(f"acceptance failed: {eid} missing _skillhub_meta.json")
    skill_text = skill.read_text(encoding="utf-8")
    import re as _re

    needs_local_refs = bool(_re.search(r"\]\(references/", skill_text)) or bool(
        _re.search(r"`references/[^`]*`", skill_text)
    )
    if needs_local_refs:
        refs = Path(skills_root) / eid / "references"
        md_refs = list(refs.glob("**/*.md")) if refs.is_dir() else []
        if not md_refs:
            raise SystemExit(
                f"acceptance failed: {eid} SKILL.md links local references/ "
                f"but no references/*.md after unzip"
            )
    print(f"ok {eid}")
PY

if [[ -f "$USER_ENV" ]]; then
  echo "credentials present: $USER_ENV"
elif [[ -f "$LEGACY_ENV" ]]; then
  echo "WARN: legacy $LEGACY_ENV still present; re-run update or wm-auth.sh to migrate" >&2
else
  echo "WARN: no credentials at $USER_ENV — open $OPEN_BASE/skillhub/creds to copy keys if needed" >&2
fi

echo "done"
