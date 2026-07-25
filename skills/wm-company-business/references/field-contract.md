# 字段对照（JSON → 叙事 / 对照表）

| 叙事 / 表头用语 | JSON 路径 | 呈现 |
|-----------------|-----------|------|
| 公司名/行业 | `snapshot.identity.*` | 头区标题；非表行 |
| ROE（TTM） | `snapshot.valuation.roe_ttm` | 有行业侧 → 对照表；否则散文；% |
| 毛利率 / 净利率（TTM） | `snapshot.valuation.gmr_ttm` / `npm_ttm` | 同上 |
| PE / PB / 五年分位 | `snapshot.valuation.*` | 默认散文；可选估值小表 |
| 市值 / 股息率 | `snapshot.valuation.mv` / `dividend_yield` | 市值：散文；股息有行业 → 可进对照表 |
| 营收/净利 TTM 同比 | `snapshot.growth.tr_yoy` / `np_yoy` | **散文**（通常无行业同比；勿凑对照列） |
| 近3年年化 | `snapshot.growth.tr_ar_3y` / `npts_ar_3y` | 双侧有则对照表；仅一侧则散文 |
| 资产负债率等 | `snapshot.debt.*` | 有行业 `tl_rate` → 可进对照表；有息负债多进散文 |
| 净现比 | `snapshot.cashflow.ocf_np`（金融已剥） | **散文**；不加 % |
| 现金流类型 | `snapshot.cashflow.kind_desc`（金融已剥） | **不进表**；解读段用类型短名（冒号前） |
| 分部名/占比 | `snapshot.business.*` | **散文**；无 share 禁精确 % |
| 行业 ROE / 负债率 | `snapshot.industry.roe` / `tl_rate` | 对照表「行业」列 |
| 行业毛/净利率 | `snapshot.industry.gmr` / `npm` | 近3年均值；对照表行业列 |
| 行业股息 | `snapshot.industry.bonus_rate` | 近3年均值 |
| 行业近3年年化 | `snapshot.industry.tr_ar_3y` / `npts_ar_3y` | 勿与 TTM 同比混称 |
| 行业内分位 | `snapshot.industry.roe_pct` / `npm_pct` / `gmr_pct` | 括号短注或解读句，勿与主数字抢格 |
| 路由 / 缺数字 | `methodology.*` / `quality.missing_fields` | 不写入读者正文 / 不写该点 |

## 准确

- 只准照抄返回值与口径；禁心算派生、禁编造行业对照。
- **口径须标清**：行业毛净利/股息/年化多为「近3年均值」，不是报告期 TTM 同比。
- 本章对照行不足 2 行 → 零表，全部进散文。
- 有精确值写精确（或源字段格式）；禁无依据 `≈`。
