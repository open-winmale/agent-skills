"""将 result-* 渲染为单文件自包含 HTML（只读；quality=pass 表 + 叙述 + 未定型损益候选）。"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

# 与 domain.catalogs 标签对齐的兜底（避免循环 import）
_GROUP_LABELS: dict[str, str] = {
    "A_key_financials": "主要会计数据",
    "B_statements": "三大报表",
    "C_segments": "主营与分部",
    "D_mda": "MD&A",
    "E_holders": "股东与股本",
    "F_dividend": "股东回报",
    "G_governance": "治理与人员",
    "H_matters": "重要事项",
    "I_audit": "审计与政策",
    "X_fossil_energy": "化石能源",
    "X_energy": "电力能源",
    "X_consumer": "消费零售",
    "X_bank": "银行",
    "X_insurance": "保险",
    "X_automobile": "汽车",
    "X_auto_electronics": "智驾电子",
    "X_nonferrous": "有色金属",
    "X_broker": "证券",
    "X_real_estate": "房地产",
    "X_pharma": "制药",
    "X_transport_infrastructure": "交运基建",
    "X_manufacturing": "制造",
    "X_building_materials": "建材",
    "X_machinery": "机械",
    "X_steel": "钢铁",
    "X_chemicals": "化工",
    "X_telecom": "电信",
    "X_internet": "互联网消费电子",
    "X_agriculture": "农业",
    "X_semiconductor": "半导体",
    "Z_generic": "未定型候选",
    "audit": "审核",
    "narratives": "叙述证据",
    "quality_board": "质量看板",
}

# 表 id → 展示分区（治理/事项优先，便于 HTML 快速适配）
_TABLE_SECTION_BUCKET: dict[str, str] = {
    "related_txn": "H_matters",
    "guarantees": "H_matters",
    "wealth_management": "H_matters",
    "construction_projects": "H_matters",
    "variance_reasons": "D_mda",
    "employees": "G_governance",
    "rd_investment": "G_governance",
    "executives": "G_governance",
    "subsidiaries": "G_governance",
    "subsidiary_financials": "G_governance",
    "equity_incentive": "G_governance",
}

_STMT_BASES = ("balance_sheet", "income_stmt", "cashflow_stmt")
_STMT_LABELS = {
    "balance_sheet": "资产负债表",
    "income_stmt": "利润表",
    "cashflow_stmt": "现金流量表",
}

_NARRATIVE_LABELS: dict[str, str] = {
    "mda_business": "业务概览",
    "mda_industry": "行业情况",
    "mda_outlook": "展望与计划",
    "risk_factors": "风险因素",
    "brand_sales": "品牌与销量",
    "dealer_network": "渠道网络",
}

_MAX_ROWS = 200  # 单表嵌入上限，防超大 related_txn 撑爆 HTML

# IFRS / CAS 损益核心科目（繁简）
_IS_CORE_LABELS = (
    "收入", "營業收入", "营业收入", "收益",
    "銷售成本", "销售成本", "营业成本", "營業成本",
    "毛利", "毛利潤", "毛利润",
)


def _table_base_id(tid: str) -> str:
    tid = str(tid or "")
    m = re.search(r"_p\d+", tid)
    if m:
        return tid[: m.start()]
    if tid.startswith("generic_merged_"):
        return tid
    return tid


def _group_label(group: str | None) -> str:
    g = group or "Z_generic"
    if g in _GROUP_LABELS:
        return _GROUP_LABELS[g]
    return g.replace("_", " ")


def _pass_ids(quality: dict) -> set[str]:
    return {
        str(t.get("id"))
        for t in (quality.get("tables") or [])
        if (t.get("verdict") or "") == "pass" and t.get("id")
    }


def _slim_row(row: dict) -> dict:
    src = row.get("source") if isinstance(row.get("source"), dict) else {}
    out: dict[str, Any] = {}
    for k, v in row.items():
        if k == "source":
            continue
        out[k] = v
    out["_page"] = src.get("page")
    out["_quote"] = src.get("quote") or ""
    out["_table"] = src.get("table")
    return out


def _load_table(result_dir: Path, file_rel: str) -> dict | None:
    path = result_dir / file_rel
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _nfkc_compact(s: str) -> str:
    try:
        import unicodedata
        return unicodedata.normalize("NFKC", s or "").replace(" ", "").replace("\u3000", "")
    except Exception:
        return (s or "").replace(" ", "")


def _row_label_blob(obj: dict) -> str:
    labels: list[str] = []
    for r in (obj.get("rows") or [])[:40]:
        if isinstance(r, dict) and r.get("item"):
            labels.append(str(r["item"]))
    if not labels:
        labels = [str(x) for x in (obj.get("sample_labels") or [])[:20]]
    return " ".join(labels)


def _looks_like_income_stmt_rows(obj: dict) -> bool:
    blob = _nfkc_compact(_row_label_blob(obj))
    if not blob:
        return False
    has_rev = any(_nfkc_compact(t) in blob for t in ("收入", "营业收入", "營業收入", "收益"))
    has_cost = any(_nfkc_compact(t) in blob for t in ("销售成本", "銷售成本", "营业成本", "營業成本"))
    has_gp = any(_nfkc_compact(t) in blob for t in ("毛利", "毛利润", "毛利潤"))
    return has_rev and has_cost and has_gp


_OPS_TITLE_TOKS = (
    "按產品", "按产品", "分產品", "分产品", "分地區", "分地区",
    "其他國家", "其他国家", "產品劃分", "产品划分", "地區", "地区",
    "來自外部客戶", "来自外部客户", "海外收入", "出口",
)


def _looks_like_ops_segment_candidate(obj: dict, ent: dict) -> bool:
    """未 pass 的产品/地区经营表：标题或行标签命中则挂经营候选。"""
    title_raw = str(obj.get("title") or "") + str(obj.get("nearby_title") or "") + str(ent.get("title") or "")
    title = _nfkc_compact(title_raw)
    # 税项/所得税分析不得冒充经营分部
    if any(_nfkc_compact(tok) in title for tok in (
        "所得稅", "所得税", "稅項", "税项", "除稅前", "除税前", "稅率", "税率",
    )):
        return False
    blob = _nfkc_compact(_row_label_blob(obj))
    if any(_nfkc_compact(tok) in blob for tok in (
        "即期所得稅", "即期所得税", "遞延所得稅", "递延所得税", "法定稅率", "法定税率",
    )):
        return False
    if any(_nfkc_compact(tok) in title for tok in _OPS_TITLE_TOKS):
        return True
    if not blob:
        return False
    has_product = any(_nfkc_compact(t) in blob for t in ("乘用車", "乘用车", "燃油車", "燃油车", "新能源"))
    has_geo = any(_nfkc_compact(t) in blob for t in ("其他國家", "其他国家", "海外", "中國", "中国"))
    has_rev = any(_nfkc_compact(t) in blob for t in ("收入", "總收入", "总收入", "毛利"))
    return bool((has_product or has_geo) and has_rev)


def _hard_failure_items(review: dict) -> set[str]:
    items: set[str] = set()
    for h in review.get("hard_failures") or []:
        if not isinstance(h, dict):
            continue
        for it in h.get("items") or []:
            items.add(str(it))
        hid = str(h.get("id") or "")
        if hid:
            items.add(hid)
    return items


def _enrich_display_title(
    source: dict,
    profile: dict,
    result_dir: Path,
    cache_id: str,
) -> str:
    """弱标题（如「2025 年度报告」）时补全公司名。"""
    raw = (source.get("title") or "").strip()
    company = (
        (profile.get("issuer") or "")
        or (profile.get("company") or "")
        or (source.get("company") or "")
        or (source.get("issuer") or "")
    ).strip()

    # report.md 首屏
    if not company:
        report = result_dir.parent / "report.md"
        if report.is_file():
            try:
                head = report.read_text(encoding="utf-8", errors="replace")[:2500]
            except OSError:
                head = ""
            m = re.search(
                r"(奇瑞汽車股份有限公司|奇瑞汽车股份有限公司|[\u4e00-\u9fff]{2,20}(?:股份有限公司|集團|集团|有限公司))",
                head,
            )
            if m:
                company = m.group(1)

    # 标题已含公司名则原样
    if company and company in raw:
        return raw
    # 弱标题：过短或仅为「…年度报告/報告」
    weak = (
        not raw
        or len(raw) < 12
        or re.fullmatch(r"\d{4}\s*年?[度度]?\s*(年度)?[报報]告", raw)
        or raw in ("年度报告", "年度報告", "中期报告", "中期報告")
    )
    if company and weak:
        period = raw if raw else (source.get("report_date") or profile.get("filing_kind") or "报告")
        return f"{company} · {period}"
    if company and not raw:
        return company
    return raw or cache_id or "财报提取"


def _pack_table_entry(
    tid: str,
    obj: dict,
    ent: dict,
    findings_by_id: dict[str, list],
    *,
    candidate: bool = False,
    candidate_kind: str = "",
    title_override: str = "",
) -> dict[str, Any]:
    cols = (obj.get("schema") or {}).get("columns") or []
    columns = [{"key": c.get("key"), "label": c.get("label") or c.get("key")} for c in cols]
    rows_raw = obj.get("rows") or []
    truncated = len(rows_raw) > _MAX_ROWS
    rows = [_slim_row(r) for r in rows_raw[:_MAX_ROWS] if isinstance(r, dict)]
    kind = candidate_kind or ("income_stmt" if candidate else "")
    if candidate and kind == "income_stmt":
        group = "B_statements"
        base = "income_stmt"
        default_title = "利润表（未定型候选）"
    elif candidate and kind == "ops":
        group = "C_segments"
        base = "ops_candidate"
        default_title = "经营分部（未定型候选）"
    else:
        base = _table_base_id(tid)
        group = (
            _TABLE_SECTION_BUCKET.get(base)
            or str(obj.get("group") or ent.get("group") or "Z_generic")
        )
        default_title = tid
        # 可读标题兜底
        _TITLE_FALLBACK = {
            "wealth_management": "委托理财与委托贷款",
            "subsidiaries": "重要子公司",
            "subsidiary_financials": "重要非全资子公司财务信息",
        }
        if not obj.get("title") and base in _TITLE_FALLBACK:
            default_title = _TITLE_FALLBACK[base]
    title = title_override or obj.get("title") or default_title
    if candidate and "未定型" not in str(title):
        title = title_override or default_title
    return {
        "id": tid,
        "title": title,
        "description": obj.get("description") or "",
        "group": group,
        "group_label": _group_label(group),
        "base": base,
        "variant": obj.get("variant") or ent.get("variant") or ("candidate" if candidate else ""),
        "candidate": candidate,
        "candidate_kind": kind if candidate else "",
        "unit_default": obj.get("unit_default") or "",
        "columns": columns,
        "rows": rows,
        "row_count": obj.get("row_count") or len(rows_raw),
        "truncated": truncated,
        "provenance": obj.get("provenance") or {},
        "findings": findings_by_id.get(tid) or [],
    }


def build_html_payload(result_dir: Path, *, cache_id: str = "") -> dict[str, Any]:
    """从 result 目录组装前端 payload（pass 表 + 叙述 + 未定型损益候选）。"""
    result_dir = Path(result_dir)
    manifest = json.loads((result_dir / "manifest.json").read_text(encoding="utf-8"))
    quality = {}
    if (result_dir / "quality.json").is_file():
        quality = json.loads((result_dir / "quality.json").read_text(encoding="utf-8"))
    review = {}
    if (result_dir / "review.json").is_file():
        review = json.loads((result_dir / "review.json").read_text(encoding="utf-8"))
    gaps = []
    if (result_dir / "gaps.json").is_file():
        gaps = json.loads((result_dir / "gaps.json").read_text(encoding="utf-8")) or []

    pass_ids = _pass_ids(quality)
    catalog_tables = (manifest.get("catalog") or {}).get("tables") or []
    catalog_narratives = (manifest.get("catalog") or {}).get("narratives") or []
    findings_by_id: dict[str, list] = {}
    for f in quality.get("python_findings") or []:
        tid = str(f.get("id") or "")
        findings_by_id.setdefault(tid, []).append({
            "verdict": f.get("verdict"),
            "reason": f.get("reason"),
            "detail": f.get("detail"),
            "adjudicated": f.get("adjudicated"),
            "adjudication_reason": f.get("adjudication_reason"),
        })

    tables_out: dict[str, Any] = {}
    nav_buckets: dict[str, list[str]] = {}

    for ent in catalog_tables:
        tid = str(ent.get("id") or "")
        if tid not in pass_ids:
            continue
        file_rel = ent.get("file") or f"tables/{tid}.json"
        obj = _load_table(result_dir, file_rel)
        if not obj:
            continue
        packed = _pack_table_entry(tid, obj, ent, findings_by_id)
        tables_out[tid] = packed
        nav_buckets.setdefault(packed["group"], []).append(tid)

    # 叙述
    narratives_out: list[dict[str, Any]] = []
    for ent in catalog_narratives:
        if not isinstance(ent, dict):
            continue
        nid = str(ent.get("id") or "")
        file_rel = ent.get("file") or f"narratives/{nid}.json"
        obj = _load_table(result_dir, file_rel) or {}
        status = obj.get("status") or ent.get("status") or "pending"
        narratives_out.append({
            "id": nid,
            "label": _NARRATIVE_LABELS.get(nid) or nid,
            "group": ent.get("group") or obj.get("group") or "D_mda",
            "status": status,
            "quote": obj.get("quote") or "",
            "page": obj.get("page"),
            "notes": obj.get("notes") or "",
            "reason": obj.get("reason") or ent.get("reason") or "",
            "method": obj.get("method") or ent.get("method") or "",
        })

    statements: dict[str, list[str]] = {b: [] for b in _STMT_BASES}
    for tid, t in tables_out.items():
        base = t.get("base") or ""
        if base in statements:
            statements[base].append(tid)
        elif any(tid == b or tid.startswith(b + "_") for b in _STMT_BASES):
            for b in _STMT_BASES:
                if tid == b or tid.startswith(b + "_"):
                    statements[b].append(tid)
                    break

    # 未定型利润表候选：review 缺 income_stmt 且存在强标签 generic
    hf_items = _hard_failure_items(review)
    if "income_stmt" in hf_items and not statements["income_stmt"]:
        best: tuple[int, str, dict, dict] | None = None
        for ent in catalog_tables:
            tid = str(ent.get("id") or "")
            if tid in pass_ids or tid in tables_out:
                continue
            if not (tid.startswith("generic_table") or tid.startswith("generic_merged")):
                # 也允许未 pass 的疑似 income 命名
                if "income" not in tid and "损益" not in tid and "利潤" not in tid and "利润" not in tid:
                    continue
            file_rel = ent.get("file") or f"tables/{tid}.json"
            obj = _load_table(result_dir, file_rel)
            if not obj or not _looks_like_income_stmt_rows(obj):
                continue
            score = int(obj.get("row_count") or len(obj.get("rows") or []))
            if best is None or score > best[0]:
                best = (score, tid, obj, ent)
        if best:
            _, tid, obj, ent = best
            packed = _pack_table_entry(
                tid, obj, ent, findings_by_id,
                candidate=True,
                candidate_kind="income_stmt",
                title_override="利润表（未定型候选）",
            )
            tables_out[tid] = packed
            statements["income_stmt"].append(tid)
            nav_buckets.setdefault("B_statements", []).append(tid)

    # 经营候选：仍未 pass 的产品/地区 generic（定型后通常已进 pass，此处作兜底）
    ops_added = 0
    for ent in catalog_tables:
        if ops_added >= 6:
            break
        tid = str(ent.get("id") or "")
        if tid in pass_ids or tid in tables_out:
            continue
        if not (tid.startswith("generic_table") or tid.startswith("generic_merged")):
            continue
        file_rel = ent.get("file") or f"tables/{tid}.json"
        obj = _load_table(result_dir, file_rel)
        if not obj or not _looks_like_ops_segment_candidate(obj, ent):
            continue
        title = obj.get("title") or ent.get("title") or tid
        packed = _pack_table_entry(
            tid, obj, ent, findings_by_id,
            candidate=True,
            candidate_kind="ops",
            title_override=f"{title}（经营候选）" if "未定型" not in str(title) and "候选" not in str(title) else title,
        )
        tables_out[tid] = packed
        nav_buckets.setdefault("C_segments", []).append(tid)
        ops_added += 1

    coverage_doc: dict[str, Any] = {}
    if (result_dir / "coverage.json").is_file():
        try:
            coverage_doc = json.loads((result_dir / "coverage.json").read_text(encoding="utf-8")) or {}
        except (OSError, json.JSONDecodeError):
            coverage_doc = {}

    coverage = list(manifest.get("coverage_groups") or [])
    group_order = list(dict.fromkeys([*coverage, *nav_buckets.keys(), "audit"]))
    nav = []
    if coverage_doc.get("items"):
        nav.append({
            "group": "quality_board",
            "label": "质量看板",
            "table_ids": [],
            "jump": "sec-coverage",
        })
    if narratives_out:
        nav.append({
            "group": "narratives",
            "label": "叙述证据",
            "table_ids": [],
            "jump": "sec-narratives",
        })
    for g in group_order:
        if g == "audit":
            nav.append({"group": "audit", "label": "审核与缺口", "table_ids": [], "jump": "sec-audit"})
            continue
        ids = nav_buckets.get(g) or []
        if not ids:
            continue
        nav.append({"group": g, "label": _group_label(g), "table_ids": ids})

    source = dict(manifest.get("source") or {})
    profile = review.get("document_profile") or {}
    # meta 侧 document_profile 兜底
    if not profile and (result_dir.parent / "meta.json").is_file():
        try:
            meta_doc = json.loads((result_dir.parent / "meta.json").read_text(encoding="utf-8"))
            profile = meta_doc.get("document_profile") or profile
        except (OSError, json.JSONDecodeError):
            pass

    cid = cache_id or manifest.get("cache_id") or result_dir.parent.name
    display_title = _enrich_display_title(source, profile, result_dir, cid)
    source["title"] = display_title
    source["display_title"] = display_title

    cov_counts = coverage_doc.get("counts") or {}
    cov_n = sum(int(v) for v in cov_counts.values()) if cov_counts else 0
    cov_high = int(cov_counts.get("high") or 0)

    return {
        "meta": {
            "cache_id": cid,
            "result": result_dir.name,
            "source": {
                "title": display_title,
                "symbol": source.get("symbol") or "",
                "report_date": source.get("report_date") or "",
                "filing_kind": source.get("filing_kind") or profile.get("filing_kind") or "",
                "industry": source.get("industry_hint") or profile.get("industry") or "",
            },
            "profile": {
                "market": profile.get("market"),
                "accounting": profile.get("accounting"),
                "industry": profile.get("industry"),
                "industry_confidence": profile.get("industry_confidence"),
                "filing_kind": profile.get("filing_kind"),
            },
            "quality_status": quality.get("status") or "missing",
            "review_status": review.get("status") or "missing",
            "pass_table_count": sum(1 for t in tables_out.values() if not t.get("candidate")),
            "catalog_table_count": len(catalog_tables),
            "narrative_count": len(narratives_out),
            "coverage_purpose_ok": coverage_doc.get("purpose_ok"),
            "coverage_high_ratio": (f"{cov_high}/{cov_n}" if cov_n else ""),
        },
        "coverage": {
            "purpose": coverage_doc.get("purpose") or "",
            "purpose_ok": coverage_doc.get("purpose_ok"),
            "counts": cov_counts,
            "items": coverage_doc.get("items") or [],
            "hard_missing_extract": coverage_doc.get("hard_missing_extract") or [],
        },
        "nav": nav,
        "statements": {
            "bases": [{"id": b, "label": _STMT_LABELS[b], "table_ids": statements[b]} for b in _STMT_BASES],
        },
        "tables": tables_out,
        "narratives": narratives_out,
        "gaps": [
            {
                "id": g.get("id"),
                "group": g.get("group"),
                "status": g.get("status"),
                "reason": g.get("reason"),
                "quote": g.get("quote"),
                "page": g.get("page"),
            }
            for g in gaps if isinstance(g, dict)
        ],
        "review": {
            "hard_failures": review.get("hard_failures") or [],
            "warnings": review.get("warnings") or [],
        },
        "findings": quality.get("python_findings") or [],
        "stmt_labels": _STMT_LABELS,
    }


def render_html_document(payload: dict[str, Any]) -> str:
    """把 payload 嵌入自包含 HTML。"""
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    payload_json = payload_json.replace("<", "\\u003c").replace(">", "\\u003e")
    title = (payload.get("meta") or {}).get("source", {}).get("title") or "财报提取"
    return _HTML_TEMPLATE.replace("__PAGE_TITLE__", html.escape(title)).replace(
        "__PAYLOAD_JSON__", payload_json
    )


def write_html_report(
    result_dir: Path,
    *,
    cache_id: str = "",
    out_path: Path | None = None,
) -> Path:
    result_dir = Path(result_dir)
    payload = build_html_payload(result_dir, cache_id=cache_id)
    doc = render_html_document(payload)
    dest = Path(out_path) if out_path else result_dir / "report.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(doc, encoding="utf-8")
    return dest


# --------------------------------------------------------------------------
# HTML template — cold slate finance viewer (system fonts, offline)
# --------------------------------------------------------------------------

_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>__PAGE_TITLE__ · 提取阅览</title>
<style>
:root {
  --ink: #0c1222;
  --muted: #5a6578;
  --paper: #f4f6f8;
  --paper-2: #eef1f4;
  --surface: #ffffff;
  --line: #d7dde5;
  --accent: #1f4e5f;
  --accent-soft: rgba(31, 78, 95, 0.10);
  --accent-deep: #163a47;
  --danger: #8f2f2f;
  --warn: #8a6a2f;
  --ok: #1f4e5f;
  --drawer-w: min(420px, 92vw);
  --side-w: 232px;
  --sans: "Avenir Next", "PingFang SC", "Hiragino Sans GB", "Noto Sans SC",
          "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  --mono: "SF Mono", "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background:
    radial-gradient(1200px 480px at 8% -10%, rgba(31, 78, 95, 0.07), transparent 55%),
    radial-gradient(900px 420px at 100% 0%, rgba(12, 18, 34, 0.04), transparent 50%),
    var(--paper);
  color: var(--ink);
  font-family: var(--sans);
  font-size: 14px;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

.hero {
  padding: 2.4rem 2rem 1.6rem;
  border-bottom: 1px solid var(--line);
  background: linear-gradient(180deg, #fafbfc 0%, rgba(244,246,248,0.85) 100%);
  position: relative;
}
.hero::after {
  content: "";
  position: absolute; left: 2rem; bottom: -1px;
  width: 4.5rem; height: 2px;
  background: var(--accent);
}
.hero-kicker {
  font-size: 0.68rem; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--muted); font-weight: 600; margin: 0 0 0.55rem;
}
.hero-brand {
  font-family: var(--sans);
  font-size: clamp(1.55rem, 2.8vw, 2.05rem);
  font-weight: 650;
  letter-spacing: -0.02em;
  margin: 0 0 0.45rem;
  max-width: 46rem;
  color: var(--ink);
}
.hero-sub {
  color: var(--muted);
  margin: 0 0 1.05rem;
  font-size: 0.92rem;
  max-width: 42rem;
}
.badges { display: flex; flex-wrap: wrap; gap: 0.45rem; align-items: center; }
.badge {
  display: inline-flex; align-items: center; gap: 0.35rem;
  padding: 0.18rem 0.6rem;
  border: 1px solid var(--line);
  border-radius: 2px;
  font-size: 0.7rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  background: var(--surface);
  font-weight: 600;
}
.badge.ok { border-color: var(--accent); color: var(--ok); background: var(--accent-soft); }
.badge.fail { border-color: var(--danger); color: var(--danger); background: rgba(143,47,47,0.07); }
.badge.miss { color: var(--muted); }
.badge.cand {
  border-color: var(--warn); color: var(--warn);
  background: rgba(138,106,47,0.08);
}

.layout {
  display: grid;
  grid-template-columns: var(--side-w) minmax(0, 1fr);
  min-height: calc(100vh - 9rem);
}
.side {
  position: sticky; top: 0; align-self: start;
  height: 100vh; overflow: auto;
  padding: 1.25rem 1rem 3rem;
  border-right: 1px solid var(--line);
  background: rgba(238, 241, 244, 0.92);
  backdrop-filter: blur(6px);
}
.side h2 {
  font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--muted); font-weight: 650; margin: 0 0 0.75rem;
}
#nav-search {
  width: 100%; padding: 0.48rem 0.65rem; margin-bottom: 1rem;
  border: 1px solid var(--line); border-radius: 2px;
  background: var(--surface); font: inherit; color: var(--ink);
}
#nav-search:focus { outline: 2px solid var(--accent-soft); border-color: var(--accent); }
.nav-group { margin-bottom: 1rem; }
.nav-group-label {
  font-size: 0.7rem; color: var(--muted); margin-bottom: 0.35rem;
  letter-spacing: 0.05em; font-weight: 600;
}
.nav-link {
  display: block; padding: 0.3rem 0.5rem; margin: 0.08rem 0;
  border-radius: 2px; color: var(--ink); cursor: pointer;
  font-size: 0.84rem; border-left: 2px solid transparent;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  transition: background 0.14s ease, border-color 0.14s ease;
}
.nav-link:hover { background: rgba(12,18,34,0.04); }
.nav-link.active {
  border-left-color: var(--accent);
  background: var(--accent-soft);
  color: var(--accent-deep);
  font-weight: 600;
}

.main { padding: 1.6rem 2rem 4rem; max-width: 960px; }
.section { margin-bottom: 2.6rem; scroll-margin-top: 1rem; animation: riseIn 0.28s ease both; }
.section:nth-of-type(2) { animation-delay: 0.04s; }
.section:nth-of-type(3) { animation-delay: 0.08s; }
.cov-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem;
}
@media (max-width: 860px) {
  .cov-grid { grid-template-columns: 1fr; }
}
.cov-col {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 0.75rem 0.85rem 0.9rem;
  min-height: 6rem;
}
.cov-col h3 {
  margin: 0 0 0.55rem;
  font-size: 0.82rem;
  letter-spacing: 0.04em;
  font-weight: 650;
}
.cov-col.high h3 { color: var(--ok); }
.cov-col.low h3 { color: var(--warn); }
.cov-col.missing h3 { color: var(--danger); }
.cov-col.nd h3 { color: var(--muted); }
.cov-item {
  font-size: 0.8rem;
  padding: 0.28rem 0;
  border-top: 1px dashed var(--line);
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
}
.cov-item:first-of-type { border-top: none; }
.cov-item .id { font-family: var(--mono); font-size: 0.74rem; }
.cov-item .pri { color: var(--muted); font-size: 0.7rem; }
.cov-empty { color: var(--muted); font-size: 0.78rem; }
@keyframes riseIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
.section h2 {
  font-family: var(--sans);
  font-size: 1.2rem; font-weight: 650;
  letter-spacing: -0.015em;
  margin: 0 0 0.3rem;
  padding-bottom: 0.45rem;
  border-bottom: 1px solid var(--line);
}
.section .hint { color: var(--muted); font-size: 0.84rem; margin: 0 0 1rem; }

.narr-grid {
  display: flex; flex-direction: column; gap: 0.75rem;
}
.narr-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-left: 3px solid var(--accent);
  padding: 0.85rem 1rem 0.95rem;
  animation: riseIn 0.32s ease both;
}
.narr-head {
  display: flex; flex-wrap: wrap; gap: 0.45rem; align-items: baseline;
  margin-bottom: 0.45rem;
}
.narr-head strong { font-size: 0.92rem; letter-spacing: -0.01em; }
.narr-quote {
  margin: 0;
  padding: 0.55rem 0.75rem;
  background: var(--paper-2);
  border-left: 2px solid rgba(31, 78, 95, 0.35);
  font-size: 0.9rem;
  color: var(--ink);
  line-height: 1.65;
}
.narr-meta { margin-top: 0.45rem; color: var(--muted); font-size: 0.78rem; }

.tabs { display: flex; flex-wrap: wrap; gap: 0.35rem; margin: 0.75rem 0 1rem; }
.tab {
  border: 1px solid var(--line); background: var(--surface); color: var(--ink);
  padding: 0.35rem 0.75rem; border-radius: 2px; cursor: pointer; font: inherit;
  transition: background 0.14s, border-color 0.14s;
}
.tab.active { border-color: var(--accent); background: var(--accent-soft); color: var(--accent-deep); font-weight: 600; }
.tab:disabled { cursor: not-allowed; }
.subtabs { display: flex; flex-wrap: wrap; gap: 0.3rem; margin-bottom: 0.75rem; }
.subtab {
  border: none; background: transparent; color: var(--muted);
  padding: 0.2rem 0.5rem; cursor: pointer; font: inherit; font-size: 0.82rem;
  border-bottom: 2px solid transparent;
}
.subtab.active { color: var(--accent-deep); border-bottom-color: var(--accent); font-weight: 600; }

.table-wrap {
  overflow: auto; max-height: min(70vh, 640px);
  border: 1px solid var(--line); background: var(--surface);
  animation: fadeIn 0.18s ease;
}
@keyframes fadeIn { from { opacity: 0.35; } to { opacity: 1; } }
.panel-title {
  font-size: 1rem; font-weight: 650; letter-spacing: -0.01em;
  display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;
}
table.data {
  width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums;
  font-family: var(--mono); font-size: 0.78rem;
}
table.data th, table.data td {
  padding: 0.42rem 0.55rem; border-bottom: 1px solid var(--line);
  text-align: left; vertical-align: top;
}
table.data th {
  position: sticky; top: 0; background: var(--paper-2);
  font-family: var(--sans); font-weight: 600; font-size: 0.7rem;
  color: var(--muted); z-index: 1; letter-spacing: 0.03em;
}
table.data tbody tr { cursor: pointer; transition: background 0.12s; }
table.data tbody tr:nth-child(even) { background: rgba(244,246,248,0.65); }
table.data tbody tr:hover { background: var(--accent-soft); }
table.data tbody tr.degraded { box-shadow: inset 3px 0 0 var(--warn); }
table.data tbody tr.candidate-row { }
table.data .page-tag {
  font-family: var(--sans); font-size: 0.68rem; color: var(--accent);
  margin-left: 0.35rem; white-space: nowrap; font-weight: 600;
}
.flag-warn {
  display: inline-block; margin-left: 0.35rem;
  color: var(--warn); font-size: 0.7rem; font-family: var(--sans);
}

.gap-list { display: flex; flex-direction: column; gap: 0.5rem; }
.gap-item {
  border: 1px solid var(--line); background: var(--surface); padding: 0.65rem 0.85rem;
  border-radius: 2px;
}
.gap-item summary { cursor: pointer; list-style: none; display: flex; gap: 0.5rem; align-items: baseline; flex-wrap: wrap; }
.gap-item summary::-webkit-details-marker { display: none; }
.status-pill {
  font-size: 0.66rem; padding: 0.1rem 0.45rem; border-radius: 2px;
  border: 1px solid var(--line); text-transform: uppercase; letter-spacing: 0.04em;
  font-weight: 650;
}
.status-pill.found { color: var(--ok); border-color: var(--accent); background: var(--accent-soft); }
.status-pill.pending, .status-pill.required { color: var(--warn); border-color: var(--warn); }
.status-pill.not_disclosed, .status-pill.not_applicable, .status-pill.not_found { color: var(--muted); }
.gap-quote {
  margin-top: 0.5rem; padding: 0.5rem 0.65rem;
  background: var(--paper-2); border-left: 2px solid var(--accent);
  font-size: 0.85rem; color: var(--ink);
}
.findings { margin-top: 1.25rem; }
.finding {
  padding: 0.45rem 0.65rem; border-left: 3px solid var(--warn);
  background: rgba(138,106,47,0.06); margin-bottom: 0.4rem; font-size: 0.85rem;
}
.footer {
  margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--line);
  color: var(--muted); font-size: 0.78rem;
}

.drawer-backdrop {
  position: fixed; inset: 0; background: rgba(12,18,34,0.32);
  opacity: 0; pointer-events: none; transition: opacity 0.2s;
  z-index: 40;
}
.drawer-backdrop.open { opacity: 1; pointer-events: auto; }
.drawer {
  position: fixed; top: 0; right: 0; width: var(--drawer-w); height: 100%;
  background: var(--surface); border-left: 1px solid var(--line);
  transform: translateX(100%); transition: transform 0.22s ease;
  z-index: 50; padding: 1.25rem 1.35rem 2rem; overflow: auto;
  box-shadow: -12px 0 32px rgba(12,18,34,0.08);
}
.drawer.open { transform: translateX(0); }
.drawer h3 {
  font-family: var(--sans); margin: 0 0 0.75rem; font-size: 1.1rem;
  font-weight: 650; letter-spacing: -0.01em;
}
.drawer dl { margin: 0; }
.drawer dt {
  font-size: 0.68rem; color: var(--muted); text-transform: uppercase;
  letter-spacing: 0.08em; margin-top: 0.85rem; font-weight: 650;
}
.drawer dd {
  margin: 0.25rem 0 0; font-family: var(--mono); font-size: 0.82rem;
  white-space: pre-wrap; word-break: break-word;
}
.drawer .close {
  position: absolute; top: 0.85rem; right: 0.85rem;
  border: none; background: transparent; font-size: 1.25rem; cursor: pointer; color: var(--muted);
}
.drawer .copy-btn {
  margin-top: 1rem; border: 1px solid var(--line); background: var(--paper);
  padding: 0.35rem 0.75rem; cursor: pointer; font: inherit; border-radius: 2px;
}
.empty { color: var(--muted); padding: 1rem 0; font-size: 0.9rem; }

@media print {
  .side, .drawer, .drawer-backdrop, #nav-search, .tabs, .subtabs { display: none !important; }
  .layout { display: block; }
  .main { max-width: none; padding: 0; }
  .table-wrap { max-height: none; overflow: visible; }
  .hero { padding: 0 0 1rem; background: none; }
  body { background: #fff; }
}
@media (max-width: 860px) {
  .layout { grid-template-columns: 1fr; }
  .side { position: relative; height: auto; border-right: none; border-bottom: 1px solid var(--line); }
}
</style>
</head>
<body>
<header class="hero" id="hero">
  <p class="hero-kicker">wm-report-extract · 阅览</p>
  <h1 class="hero-brand" id="hero-title"></h1>
  <p class="hero-sub" id="hero-sub"></p>
  <div class="badges" id="hero-badges"></div>
</header>
<div class="layout">
  <aside class="side" id="side">
    <h2>目录 <kbd style="font-weight:400;opacity:.55">/</kbd></h2>
    <input id="nav-search" type="search" placeholder="搜索表…" autocomplete="off"/>
    <nav id="nav"></nav>
  </aside>
  <main class="main" id="main">
    <section class="section" id="sec-coverage">
      <h2>质量看板</h2>
      <p class="hint">深研必要集四态：高可靠 / 低可靠 / 应提未提 / 应提未披露。可选阅览，权威产物为 coverage.json。</p>
      <div class="cov-grid" id="cov-panel"></div>
    </section>
    <section class="section" id="sec-narratives">
      <h2>叙述证据</h2>
      <p class="hint">Agent 闭环 / narrative-scan 落盘的可复核 quote；点击页码角标无额外动作。</p>
      <div class="narr-grid" id="narr-panel"></div>
    </section>
    <section class="section" id="sec-statements">
      <h2>三大报表</h2>
      <p class="hint">默认仅 quality=pass。缺定型时若检出强标签候选，以「未定型候选」展示（不改质量门）。点击行查看溯源。</p>
      <div class="tabs" id="stmt-tabs"></div>
      <div class="subtabs" id="stmt-subtabs"></div>
      <div id="stmt-panel"></div>
    </section>
    <section class="section" id="sec-other">
      <h2>经营、治理与事项</h2>
      <p class="hint">分部、产销、股东、治理、关联交易/担保、理财、子公司及行业晋升表。</p>
      <div id="other-panel"></div>
    </section>
    <section class="section" id="sec-audit">
      <h2>审核与缺口</h2>
      <p class="hint">gaps 终态与 QA findings；只读，不在此改数。</p>
      <div id="audit-hard"></div>
      <div class="gap-list" id="gap-list"></div>
      <div class="findings" id="findings"></div>
    </section>
    <footer class="footer" id="footer"></footer>
  </main>
</div>
<div class="drawer-backdrop" id="backdrop"></div>
<aside class="drawer" id="drawer" aria-hidden="true">
  <button class="close" id="drawer-close" aria-label="关闭">×</button>
  <h3>溯源</h3>
  <dl id="drawer-body"></dl>
  <button class="copy-btn" id="drawer-copy">复制 quote</button>
</aside>
<script type="application/json" id="payload">__PAYLOAD_JSON__</script>
<script>
(function () {
  const payload = JSON.parse(document.getElementById("payload").textContent);
  const meta = payload.meta || {};
  const tables = payload.tables || {};
  const nav = payload.nav || [];
  const narratives = payload.narratives || [];
  const statements = (payload.statements && payload.statements.bases) || [];
  let activeStmt = null;
  let activeTableId = null;
  let drawerQuote = "";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function badge(label, status) {
    const cls = status === "pass" ? "ok" : (status === "fail" ? "fail" : "miss");
    return `<span class="badge ${cls}">${esc(label)} · ${esc(status)}</span>`;
  }

  function renderHero() {
    const src = meta.source || {};
    document.getElementById("hero-title").textContent = src.title || "财报提取阅览";
    const bits = [
      src.symbol && `代码 ${src.symbol}`,
      src.report_date && `报告期 ${src.report_date}`,
      (meta.profile && meta.profile.market) && String(meta.profile.market).toUpperCase(),
      src.filing_kind && src.filing_kind,
      src.industry && `行业 ${src.industry}`,
      `${meta.pass_table_count || 0} 张 pass 表`,
      meta.narrative_count != null && `${meta.narrative_count} 条叙述`,
      meta.coverage_high_ratio && `覆盖 high ${meta.coverage_high_ratio}`,
    ].filter(Boolean);
    document.getElementById("hero-sub").textContent = bits.join(" · ");
    let badges = badge("quality", meta.quality_status) + badge("review", meta.review_status);
    if (meta.coverage_purpose_ok === true) badges += badge("purpose", "pass");
    else if (meta.coverage_purpose_ok === false) badges += badge("purpose", "fail");
    document.getElementById("hero-badges").innerHTML = badges;
    document.getElementById("footer").textContent =
      `数据来源：${src.title || "—"}（报告期 ${src.report_date || "—"}；PDF 页码见正文角标；cache ${meta.cache_id || "—"}；result ${meta.result || "—"}）`;
  }

  function renderNav(filter) {
    const q = (filter || "").trim().toLowerCase();
    const el = document.getElementById("nav");
    let html = "";
    nav.forEach(g => {
      if (g.jump) {
        html += `<div class="nav-group" data-group="${esc(g.group)}">
          <div class="nav-group-label">${esc(g.label)}</div>
          <div class="nav-link" data-jump="${esc(g.jump)}">${esc(g.label)}</div>
        </div>`;
        return;
      }
      const ids = (g.table_ids || []).filter(id => {
        if (!q) return true;
        const t = tables[id] || {};
        return (id + " " + (t.title || "")).toLowerCase().includes(q);
      });
      if (!ids.length && q) return;
      html += `<div class="nav-group" data-group="${esc(g.group)}">
        <div class="nav-group-label">${esc(g.label)}</div>`;
      ids.forEach(id => {
        const t = tables[id] || {};
        const mark = t.candidate ? " · 候选" : "";
        html += `<div class="nav-link" data-table="${esc(id)}" title="${esc(t.title || id)}">${esc(t.title || id)}${mark}</div>`;
      });
      html += `</div>`;
    });
    el.innerHTML = html || `<div class="empty">无匹配</div>`;
  }

  function renderCoverage() {
    const mount = document.getElementById("cov-panel");
    const sec = document.getElementById("sec-coverage");
    const cov = payload.coverage || {};
    const items = cov.items || [];
    if (!items.length) {
      sec.style.display = "none";
      return;
    }
    sec.style.display = "";
    const buckets = {
      high: { title: "高可靠", cls: "high", items: [] },
      low: { title: "低可靠", cls: "low", items: [] },
      missing_extract: { title: "应提未提", cls: "missing", items: [] },
      not_disclosed: { title: "应提未披露", cls: "nd", items: [] },
    };
    items.forEach(it => {
      const st = it.state || "";
      if (st === "not_applicable") return;
      const b = buckets[st] || buckets.low;
      b.items.push(it);
    });
    mount.innerHTML = Object.keys(buckets).map(k => {
      const b = buckets[k];
      const body = b.items.length
        ? b.items.map(it => `<div class="cov-item"><span class="id">${esc(it.id)}</span><span class="pri">${esc(it.priority || "")} · ${esc(it.kind || "")}</span></div>`).join("")
        : `<div class="cov-empty">（无）</div>`;
      return `<div class="cov-col ${b.cls}"><h3>${esc(b.title)} · ${b.items.length}</h3>${body}</div>`;
    }).join("");
  }

  function renderNarratives() {
    const mount = document.getElementById("narr-panel");
    const sec = document.getElementById("sec-narratives");
    if (!narratives.length) {
      sec.style.display = "none";
      return;
    }
    sec.style.display = "";
    mount.innerHTML = narratives.map((n, i) => {
      const st = n.status || "pending";
      const quote = n.quote
        ? `<blockquote class="narr-quote">${esc(n.quote)}</blockquote>`
        : `<div class="empty">${esc(n.reason || "无 quote")}</div>`;
      const notes = n.notes ? `<div class="narr-meta">${esc(n.notes)}</div>` : "";
      return `<article class="narr-card" style="animation-delay:${0.03 * i}s">
        <div class="narr-head">
          <span class="status-pill ${esc(st)}">${esc(st)}</span>
          <strong>${esc(n.label || n.id)}</strong>
          ${n.page != null ? `<span class="page-tag">p${esc(n.page)}</span>` : ""}
        </div>
        ${quote}${notes}
      </article>`;
    }).join("");
  }

  function openDrawer(row) {
    drawerQuote = row._quote || "";
    const body = document.getElementById("drawer-body");
    body.innerHTML = `
      <dt>科目 / 行</dt><dd>${esc(row.item || "—")}</dd>
      <dt>页码</dt><dd>${esc(row._page != null ? "p" + row._page : "—")}</dd>
      <dt>表索引</dt><dd>${esc(row._table != null ? row._table : "—")}</dd>
      <dt>Quote</dt><dd>${esc(row._quote || "（无 quote）")}</dd>`;
    document.getElementById("drawer").classList.add("open");
    document.getElementById("backdrop").classList.add("open");
    document.getElementById("drawer").setAttribute("aria-hidden", "false");
  }

  function closeDrawer() {
    document.getElementById("drawer").classList.remove("open");
    document.getElementById("backdrop").classList.remove("open");
    document.getElementById("drawer").setAttribute("aria-hidden", "true");
  }

  function renderTable(tid, mountId) {
    const t = tables[tid];
    const mount = document.getElementById(mountId);
    if (!t) {
      mount.innerHTML = `<div class="empty">无表 ${esc(tid)}</div>`;
      return;
    }
    const cols = t.columns || [];
    const degraded = (t.findings || []).some(f =>
      f.verdict === "degraded" && (!f.adjudicated || f.adjudicated === "real")
    );
    let head = "<tr>" + cols.map(c => `<th>${esc(c.label || c.key)}</th>`).join("") + "<th>页</th></tr>";
    let body = (t.rows || []).map(r => {
      const cells = cols.map(c => {
        const key = c.key;
        let val = r[key];
        if (key === "item" || (cols[0] && key === cols[0].key)) {
          return `<td>${esc(val)}${degraded ? '<span class="flag-warn">需复核</span>' : ""}</td>`;
        }
        return `<td>${esc(val)}</td>`;
      }).join("");
      const page = r._page != null ? `<span class="page-tag">p${esc(r._page)}</span>` : "";
      return `<tr class="${degraded ? "degraded" : ""}" data-row="${encodeURIComponent(JSON.stringify(r))}">${cells}<td>${page}</td></tr>`;
    }).join("");
    const trunc = t.truncated ? `<p class="hint">已截断至前 ${t.rows.length} / ${t.row_count} 行</p>` : "";
    const candTag = t.candidate
      ? `<span class="badge cand">未定型候选</span>` : "";
    const varTag = t.variant && t.variant !== "primary" && t.variant !== "candidate"
      ? `<span class="badge miss" style="font-size:11px">${esc(t.variant)}</span>` : "";
    const titleHtml = `<h3 class="panel-title">${esc(t.title || tid)}${candTag}${varTag}</h3>`;
    const findList = t.findings || [];
    const adjN = findList.filter(f => f.adjudicated === "rule_limitation").length;
    const pendingN = findList.filter(f => f.verdict === "degraded" && (!f.adjudicated || f.adjudicated === "real")).length;
    const adjSummary = findList.length
      ? `<p class="hint">发现 ${findList.length} 条：已仲裁(rule_limitation) ${adjN} · 待复核/确有问题 ${pendingN}</p>`
      : "";
    const findHtml = findList.map(f =>
      `<div class="finding">${esc(f.reason || "")} — ${esc(f.detail || "")}${f.adjudicated ? `（已仲裁：${esc(f.adjudicated)}${f.adjudication_reason ? " · " + esc(f.adjudication_reason) : ""}）` : ""}</div>`
    ).join("");
    const candHint = t.candidate
      ? (t.candidate_kind === "ops"
        ? `<p class="hint">经营候选：未纳入 quality=pass，仅供阅览核对。</p>`
        : `<p class="hint">此表未通过定型签名，仅供阅览；勿当作正式 income_stmt 下游输入。</p>`)
      : "";
    mount.innerHTML = `${titleHtml}${candHint}${trunc}${adjSummary}<div class="table-wrap"><table class="data"><thead>${head}</thead><tbody>${body}</tbody></table></div>${findHtml}`;
    mount.querySelectorAll("tbody tr").forEach(tr => {
      tr.addEventListener("click", () => {
        try { openDrawer(JSON.parse(decodeURIComponent(tr.getAttribute("data-row")))); } catch (e) {}
      });
    });
    activeTableId = tid;
    document.querySelectorAll(".nav-link").forEach(a => {
      a.classList.toggle("active", a.getAttribute("data-table") === tid);
    });
  }

  function renderStmtTabs() {
    const tabs = document.getElementById("stmt-tabs");
    tabs.innerHTML = statements.map(s => {
      const n = (s.table_ids || []).length;
      const dis = n ? "" : " disabled style=\"opacity:.4\"";
      const hasCand = (s.table_ids || []).some(id => tables[id] && tables[id].candidate);
      const label = hasCand ? `${s.label} · 候选` : s.label;
      return `<button class="tab" data-stmt="${esc(s.id)}"${dis}>${esc(label)} (${n})</button>`;
    }).join("");
    const first = statements.find(s => (s.table_ids || []).length);
    if (first) selectStmt(first.id);
    else document.getElementById("stmt-panel").innerHTML = `<div class="empty">无 pass 三表</div>`;
  }

  function selectStmt(base) {
    activeStmt = base;
    try { sessionStorage.setItem("wm-html-stmt", base); } catch (e) {}
    document.querySelectorAll("#stmt-tabs .tab").forEach(b => {
      b.classList.toggle("active", b.getAttribute("data-stmt") === base);
    });
    const spec = statements.find(s => s.id === base);
    const ids = (spec && spec.table_ids) || [];
    const sub = document.getElementById("stmt-subtabs");
    sub.innerHTML = ids.map((id, i) => {
      const t = tables[id] || {};
      const label = t.title || id;
      return `<button class="subtab${i === 0 ? " active" : ""}" data-tid="${esc(id)}">${esc(label)}</button>`;
    }).join("");
    if (ids[0]) renderTable(ids[0], "stmt-panel");
  }

  function renderOther() {
    const stmtIds = new Set();
    statements.forEach(s => (s.table_ids || []).forEach(id => stmtIds.add(id)));
    const otherIds = Object.keys(tables).filter(id => !stmtIds.has(id));
    const mount = document.getElementById("other-panel");
    if (!otherIds.length) {
      mount.innerHTML = `<div class="empty">无其它 pass 表</div>`;
      return;
    }
    // 治理/事项优先，便于理财·子公司·关联交易快速找到
    const pri = { G_governance: 0, H_matters: 1, D_mda: 2, C_segments: 3, E_holders: 4 };
    otherIds.sort((a, b) => {
      const ga = (tables[a] && tables[a].group) || "Z";
      const gb = (tables[b] && tables[b].group) || "Z";
      const pa = pri[ga] != null ? pri[ga] : 9;
      const pb = pri[gb] != null ? pri[gb] : 9;
      if (pa !== pb) return pa - pb;
      return String((tables[a] && tables[a].title) || a).localeCompare(
        String((tables[b] && tables[b].title) || b), "zh");
    });
    let html = `<div class="tabs" id="other-tabs">` +
      otherIds.map((id, i) => {
        const t = tables[id];
        const gl = (t && t.group_label) ? ` · ${t.group_label}` : "";
        return `<button class="tab${i === 0 ? " active" : ""}" data-tid="${esc(id)}">${esc((t && t.title) || id)}${esc(gl)}</button>`;
      }).join("") + `</div><div id="other-table"></div>`;
    mount.innerHTML = html;
    renderTable(otherIds[0], "other-table");
    mount.querySelectorAll(".tab").forEach(b => {
      b.addEventListener("click", () => {
        mount.querySelectorAll(".tab").forEach(x => x.classList.remove("active"));
        b.classList.add("active");
        renderTable(b.getAttribute("data-tid"), "other-table");
      });
    });
  }

  function renderAudit() {
    const rev = payload.review || {};
    const hard = rev.hard_failures || [];
    const hardEl = document.getElementById("audit-hard");
    if (hard.length) {
      hardEl.innerHTML = hard.map(h =>
        `<div class="finding" style="border-left-color:var(--danger)">硬挂 · ${esc(h.id || "")} — ${esc(h.reason || "")}
        ${(h.items || []).length ? "（" + esc((h.items || []).join(", ")) + "）" : ""}</div>`
      ).join("");
    } else {
      hardEl.innerHTML = `<div class="empty">无 hard_failures</div>`;
    }
    const gaps = payload.gaps || [];
    document.getElementById("gap-list").innerHTML = gaps.map(g => {
      const st = g.status || "pending";
      return `<details class="gap-item">
        <summary>
          <span class="status-pill ${esc(st)}">${esc(st)}</span>
          <strong>${esc(g.id || "")}</strong>
          <span style="color:var(--muted);font-size:.85rem">${esc(g.reason || "")}</span>
          ${g.page != null ? `<span class="page-tag">p${esc(g.page)}</span>` : ""}
        </summary>
        ${g.quote ? `<div class="gap-quote">${esc(g.quote)}</div>` : (st === "pending" || st === "required" ? `<div class="empty">待 text_scan / auto-heal</div>` : "")}
      </details>`;
    }).join("") || `<div class="empty">无 gaps</div>`;
    const findings = payload.findings || [];
    document.getElementById("findings").innerHTML = findings.length
      ? `<h3 style="font-size:1.02rem;font-weight:650;letter-spacing:-0.01em">QA findings</h3>` +
        findings.map(f => `<div class="finding">${esc(f.id)} · ${esc(f.verdict)} · ${esc(f.reason)} — ${esc(f.detail || "")}</div>`).join("")
      : "";
  }

  document.getElementById("stmt-tabs").addEventListener("click", e => {
    const b = e.target.closest(".tab");
    if (b && b.getAttribute("data-stmt") && !b.disabled) selectStmt(b.getAttribute("data-stmt"));
  });
  document.getElementById("stmt-subtabs").addEventListener("click", e => {
    const b = e.target.closest(".subtab");
    if (!b) return;
    document.querySelectorAll("#stmt-subtabs .subtab").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    renderTable(b.getAttribute("data-tid"), "stmt-panel");
  });
  document.getElementById("nav").addEventListener("click", e => {
    const jump = e.target.closest("[data-jump]");
    if (jump) {
      const target = document.getElementById(jump.getAttribute("data-jump"));
      if (target) target.scrollIntoView({ behavior: "smooth" });
      return;
    }
    const a = e.target.closest("[data-table]");
    if (!a) return;
    const tid = a.getAttribute("data-table");
    const t = tables[tid];
    if (!t) return;
    const base = t.base;
    if (["balance_sheet", "income_stmt", "cashflow_stmt"].includes(base) ||
        ["balance_sheet", "income_stmt", "cashflow_stmt"].some(b => tid === b || tid.startsWith(b + "_")) ||
        (t.candidate && t.candidate_kind === "income_stmt")) {
      let b = base;
      if (!["balance_sheet", "income_stmt", "cashflow_stmt"].includes(b)) {
        b = (t.candidate && t.candidate_kind === "income_stmt") ? "income_stmt"
          : ["balance_sheet", "income_stmt", "cashflow_stmt"].find(x => tid === x || tid.startsWith(x + "_"));
      }
      selectStmt(b);
      document.querySelectorAll("#stmt-subtabs .subtab").forEach(x => {
        const on = x.getAttribute("data-tid") === tid;
        x.classList.toggle("active", on);
      });
      renderTable(tid, "stmt-panel");
      document.getElementById("sec-statements").scrollIntoView({ behavior: "smooth" });
    } else {
      document.getElementById("sec-other").scrollIntoView({ behavior: "smooth" });
      const tab = document.querySelector(`#other-tabs .tab[data-tid="${CSS.escape(tid)}"]`);
      if (tab) tab.click();
      else renderTable(tid, "other-table");
    }
  });
  document.getElementById("nav-search").addEventListener("input", e => renderNav(e.target.value));
  document.getElementById("backdrop").addEventListener("click", closeDrawer);
  document.getElementById("drawer-close").addEventListener("click", closeDrawer);
  document.getElementById("drawer-copy").addEventListener("click", () => {
    if (drawerQuote) navigator.clipboard.writeText(drawerQuote).catch(() => {});
  });
  document.addEventListener("keydown", e => {
    if (e.key === "/" && document.activeElement.tagName !== "INPUT") {
      e.preventDefault();
      document.getElementById("nav-search").focus();
    }
    if (e.key === "Escape") closeDrawer();
  });

  renderHero();
  renderNav("");
  renderCoverage();
  renderNarratives();
  renderStmtTabs();
  try {
    const saved = sessionStorage.getItem("wm-html-stmt");
    if (saved && statements.some(s => s.id === saved && (s.table_ids || []).length)) selectStmt(saved);
  } catch (e) {}
  renderOther();
  renderAudit();
})();
</script>
</body>
</html>
"""
