# 字段对照（JSON → 叙事 / 估值表 / 对照表）

| 叙事 / 表头用语 | JSON 路径 | 呈现 |
|-----------------|-----------|------|
| 公司名/行业 | `snapshot.identity.*` | 头区标题；非表行 |
| PE / PB（日） | `snapshot.valuation.pe_daily` / `pb_daily` | **估值小表主行** |
| PR / 市赚率 | `snapshot.valuation.pr_last`（或 `pr_ttm`）/ `pr_avg` | **同卡角度**；metrics_bar「PR(市赚率)」；人眼全页 → deeplink `company.undervalue` / `pr` |
| PE / PB 五年分位 | `snapshot.valuation.pe_pct5y` / `pb_pct5y` | 估值小表第三列 |
| 盈利收益率 | `snapshot.valuation.earnings_yield` | 绝对锚；散文 |
| 市值 | `snapshot.valuation.mv` | 市值散文（HK 标报表币种） |
| ROE（TTM / IPO均） | `snapshot.valuation.roe_ttm` / `roe_avgipo` | 有行业侧 → 对照表；否则散文 |
| 股息率 / 分红率 | `snapshot.valuation.dividend_yield` / `payout` | 散文；红利溢价透镜 |
| FCF 收益率 | `snapshot.valuation.fcf_yield` | 绝对锚；散文；**金融剥离** |
| 商誉/固定资产占比 | `snapshot.valuation.goodwill_ratio` / `ppe_ratio` | 价值陷阱风险；散文；**金融剥离** |
| 席勒 PE 均值 | `snapshot.valuation.shiller_pe_avg10` / `shiller_pe_avg5` | **仅 flags.shiller_fork=true 时**一句；**金融剥离** |
| 席勒分叉比 | `snapshot.valuation.shiller_fork_ratio` | 同上 |
| 营收/净利同比 | `snapshot.growth.tr_yoy` / `np_yoy` | 散文；分母效应诊断 |
| 行业 PE/PB/ROE | `snapshot.industry.pe` / `pb` / `roe` | 对照表「行业」列 |
| 行业股息 | `snapshot.industry.bonus_rate` | 近3年均值；散文 |
| 行业 PE 10年均值 | `snapshot.industry.pe_avg10` | 对照表行业列 |
| 诊断旗标 | `flags.*` | **专名门依据**；语义键（`fake_cheap_risk`/`harvest_candidate`/`shiller_fork`/`growth_decel`） |
| 裁决枚举 | `sections[].facts.verdict_enum` | 核心观点#2 必含整词 |
| 路由 / 缺数字 | `methodology.*` / `quality.missing_fields` | 不写入读者正文 / 不写该点 |

## 准确

- 只准照抄返回值与口径；禁心算派生、禁编造行业对照。
- **口径须标清**：行业 PE/PB/ROE 多为「整体法 TTM」或「近3/10年均值」，不是报告期 TTM 同比。
- 本章对照行不足 2 行 → 零对照表，全部进散文或估值小表。
- 有精确值写精确；禁无依据 `≈`。

## 诊断专名门（flags 交叉校验）

| 正文出现 | 须 `flags` 含 |
|----------|---------------|
| 分母扩张 / 假便宜 | `fake_cheap_risk=true` |
| 分母收缩 / 假贵 | `fake_expensive_risk=true` |
| 席勒分叉 / 席勒分叉显著 | `shiller_fork=true` |
| 收割候选 | `harvest_candidate=true` |

无对应 flag → 禁点名；只写分位数字 + "利润分母效应" + ≠低估/≠高估。
