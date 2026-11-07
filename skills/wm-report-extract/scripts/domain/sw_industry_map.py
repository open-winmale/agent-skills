"""申万行业码/名 → wm-report-extract 内部 industry key（按码与品类，禁止发行人特判）。"""
from __future__ import annotations

import re
from typing import Any

# 申万 2021 一级行业码前两位（220000→22）及平台 industry.S22 / S220301 前缀
# 未单列的 L1 不映射（返回 null），避免瞎猜。
SW_L1_CODE_TO_INDUSTRY: dict[str, str] = {
    "11": "agriculture",
    "22": "chemicals",
    "23": "steel",
    "24": "nonferrous",
    "28": "automobile",
    "34": "consumer",  # 食品饮料
    "37": "pharma",
    "42": "transport_infrastructure",
    "43": "real_estate",
    "45": "consumer",  # 商贸零售
    "48": "bank",
    "61": "building_materials",
    "64": "machinery",
    "71": "internet_consumer_electronics",
    "73": "telecom",
    "74": "fossil_energy",  # 煤炭
    "75": "fossil_energy",  # 石油石化
}

# 中文名（含 L1/L2/L3）→ 内部 industry；长词优先匹配
SW_NAME_TO_INDUSTRY: list[tuple[str, str]] = [
    # 金融
    ("国有大型银行", "bank"),
    ("股份制银行", "bank"),
    ("城商行", "bank"),
    ("农商行", "bank"),
    ("银行", "bank"),
    ("保险", "insurance"),
    ("寿险", "insurance"),
    ("财险", "insurance"),
    ("证券", "broker"),
    ("券商", "broker"),
    # 化工（含农化/钾肥品类词——按申万三级，非发行人特判）
    ("基础化工", "chemicals"),
    ("化学原料", "chemicals"),
    ("化学制品", "chemicals"),
    ("农化制品", "chemicals"),
    ("化学纤维", "chemicals"),
    ("钾肥", "chemicals"),
    ("磷肥", "chemicals"),
    ("氮肥", "chemicals"),
    ("复合肥", "chemicals"),
    ("氟化工", "chemicals"),
    ("煤化工", "chemicals"),
    ("纯碱", "chemicals"),
    ("氯碱", "chemicals"),
    # 有色 / 钢铁 / 化石 / 电力
    ("有色金属", "nonferrous"),
    ("工业金属", "nonferrous"),
    ("能源金属", "nonferrous"),
    ("贵金属", "nonferrous"),
    ("钢铁", "steel"),
    ("煤炭", "fossil_energy"),
    ("石油石化", "fossil_energy"),
    ("油气", "fossil_energy"),
    ("电力", "energy"),
    ("火电", "energy"),
    ("水电", "energy"),
    ("公用事业", "energy"),
    # 汽车 / 制造 / 医药 / 消费 / 交运 / 地产 / 建材 / 机械 / 通信 / 电子
    ("汽车整车", "automobile"),
    ("商用车", "automobile"),
    ("乘用车", "automobile"),
    ("汽车零部件", "automobile"),
    ("汽车", "automobile"),
    ("化学制药", "pharma"),
    ("中药", "pharma"),
    ("生物制品", "pharma"),
    ("医药生物", "pharma"),
    ("医疗器械", "pharma"),
    ("白酒", "consumer"),
    ("啤酒", "consumer"),
    ("食品饮料", "consumer"),
    ("商贸零售", "consumer"),
    ("一般零售", "consumer"),
    ("高速公路", "transport_infrastructure"),
    ("港口", "transport_infrastructure"),
    ("航运", "transport_infrastructure"),
    ("交通运输", "transport_infrastructure"),
    ("房地产开发", "real_estate"),
    ("房地产", "real_estate"),
    ("水泥", "building_materials"),
    ("玻纤", "building_materials"),
    ("建筑材料", "building_materials"),
    ("专用设备", "machinery"),
    ("机械设备", "machinery"),
    ("通信设备", "telecom"),
    ("通信服务", "telecom"),
    ("通信", "telecom"),
    ("半导体", "semiconductor"),
    ("元件", "semiconductor"),
    ("消费电子", "internet_consumer_electronics"),
    ("计算机", "internet_consumer_electronics"),
    ("软件开发", "internet_consumer_electronics"),
    ("种植业", "agriculture"),
    ("养殖业", "agriculture"),
    ("农林牧渔", "agriculture"),
]


def _norm_sw_code(code: str | None) -> str:
    """industry.S220301 / S22 / 220000 / 220301 → 数字串。"""
    if not code:
        return ""
    s = str(code).strip()
    s = re.sub(r"^industry\.", "", s, flags=re.I)
    s = re.sub(r"^S", "", s, flags=re.I)
    digits = re.sub(r"\D", "", s)
    return digits


def _l1_prefix(digits: str) -> str:
    """6 位申万码取前 2 位；平台 S22 / S2203 等同理。"""
    if len(digits) >= 2:
        return digits[:2]
    return digits


def map_sw_industry(
    *,
    industry_l1: str | None = None,
    industry_l2: str | None = None,
    industry_l3: str | None = None,
    names: list[str] | None = None,
) -> dict[str, Any]:
    """映射申万字段到 extract industry。

    Returns:
      extract_industry | None, map_level, confidence, matched (证据)
    """
    name_blob = " ".join(
        str(x) for x in (
            list(names or [])
            + [industry_l1 or "", industry_l2 or "", industry_l3 or ""]
        ) if x
    )
    # 1) 中文名（细 → 粗：表已按长词优先排列）
    for kw, ind in SW_NAME_TO_INDUSTRY:
        if kw and kw in name_blob:
            level = "l3" if industry_l3 and kw in str(industry_l3) else (
                "l2" if industry_l2 and kw in str(industry_l2) else "l1"
            )
            conf = 0.92 if level == "l3" else (0.88 if level == "l2" else 0.82)
            # 非银金融笼统名不够定 broker/insurance
            if kw == "非银金融":
                continue
            return {
                "extract_industry": ind,
                "map_level": level,
                "confidence": conf,
                "matched": {"name": kw, "blob": name_blob[:80]},
            }

    # 2) 码前缀（L3→L2→L1）
    for level, raw in (("l3", industry_l3), ("l2", industry_l2), ("l1", industry_l1)):
        digits = _norm_sw_code(raw)
        if not digits:
            continue
        # 非银金融 49：需名字区分；纯码不够细则跳过
        pref = _l1_prefix(digits)
        if pref == "49":
            continue
        ind = SW_L1_CODE_TO_INDUSTRY.get(pref)
        if ind:
            conf = 0.9 if level == "l3" else (0.85 if level == "l2" else 0.8)
            return {
                "extract_industry": ind,
                "map_level": level,
                "confidence": conf,
                "matched": {"code": raw, "l1_prefix": pref},
            }

    return {
        "extract_industry": None,
        "map_level": None,
        "confidence": 0.0,
        "matched": {},
    }


def merge_platform_and_pdf_industry(
    pdf_hint: dict | None,
    platform_map: dict | None,
    *,
    platform_raw: dict | None = None,
) -> tuple[dict, list[dict]]:
    """合并平台映射与 PDF detect_industry。

    平台有有效映射时驱动 industry；冲突写入 anomaly。
    """
    anomalies: list[dict] = []
    pdf = dict(pdf_hint or {})
    pdf_ind = (pdf.get("industry") or "").strip() or None
    pmap = platform_map or {}
    plat_ind = (pmap.get("extract_industry") or "").strip() or None

    if not plat_ind:
        out = dict(pdf)
        out.setdefault("source", "pdf")
        if platform_raw is not None and not pmap.get("extract_industry"):
            # 调用成功但未映射 / 或调用失败由上层标 unavailable
            if platform_raw.get("ok") and not plat_ind:
                anomalies.append({
                    "code": "industry_platform_unmapped",
                    "detail": "wm-company-card 有申万码但未落入内部 industry 目录",
                    "platform": {
                        "l1": platform_raw.get("industry_l1"),
                        "l2": platform_raw.get("industry_l2"),
                        "l3": platform_raw.get("industry_l3"),
                    },
                })
        return out, anomalies

    out: dict[str, Any] = {
        "industry": plat_ind,
        "confidence": max(float(pmap.get("confidence") or 0.75), 0.75),
        "source": "platform",
        "map_level": pmap.get("map_level"),
        "matched": dict(pmap.get("matched") or {}),
        "platform": {
            "industry_l1": (platform_raw or {}).get("industry_l1"),
            "industry_l2": (platform_raw or {}).get("industry_l2"),
            "industry_l3": (platform_raw or {}).get("industry_l3"),
            "names": (platform_raw or {}).get("names") or [],
        },
    }
    if pdf_ind:
        out["pdf_industry"] = pdf_ind
        out["pdf_confidence"] = pdf.get("confidence")
        out["pdf_matched"] = pdf.get("matched")
        if pdf_ind != plat_ind:
            out["source"] = "platform_conflict"
            anomalies.append({
                "code": "industry_source_conflict",
                "detail": f"平台={plat_ind} PDF={pdf_ind}，adapt/promote 以平台为准",
                "platform": plat_ind,
                "pdf": pdf_ind,
            })
    return out, anomalies
