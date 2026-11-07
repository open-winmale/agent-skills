---
name: wm-report-extract
display_name: "财报提取 Financial Report Extractor"
version: 0.8.1
description: 财报 PDF（年报/半年报/季报，A 股 + 港股 IFRS）核心信息提取：默认全量核心包，点名则按需 resolve。程序只做可机器回验的确定性工作（双轨转换、可提取性 meta、全表 records、勾稽/数值存在性/quote 回验）；found 仅当 quote 回验成功。语义判断由 AI 以顶级投资专家身份把关。每个数值带页码与原文 quote；无 quality.json 不得给下游。Standalone——`fetch --pdf-url` 无需 API key 即可全链路运行；可选接入 WinMale 平台启用 symbol 模式。Use when the user asks to extract or locate data in a financial report PDF (annual/semi-annual/quarterly), e.g. 货币资金、前十大股东、分红方案、全量核心数据、第 N 页内容。
---

# 财报提取

对财报 PDF（年报/半年报/季报）产出可溯源（页码+quote）的证据包。**默认全量**核心包；用户**点名数据项**时走按需路径。两种模式共用格式/行业 know-how 与「规划 → 提取 → 验证」。

## 财报 know-how（规划前置，两种模式都要）

动手前提完这四问；答不出先 `scan --summary`，禁止按工商年报模板硬套。

| 维度 | 必须弄清 |
|------|----------|
| **报告类型** | 年报 / 半年报 / 一季报 / 三季报。季报不要硬升年报才有的组（完整 MD&A、审计、分红预案） |
| **准则与市场** | A 股 CAS「第 X 节」；港股 IFRS 简繁签名；**合并表 vs 母公司表不是续表** |
| **版式** | 有框线→PyMuPDF；三线表→Docling；节标签前置列；跨页续 vs 新表标题阻断；物理页 vs 目录印刷页 |
| **行业/原型** | 先定七原型 A–G（见 [analysis-needs.md](references/analysis-needs.md)），再升权。银行禁止合同负债 hard；thin 行业无 hard 清单 |

细节按需打开 references（一次最多 2 个）：E1 → `adapt_plan` + analysis-needs 对应原型节；E2 → workflow；E4 → provenance。

## 规划 → 提取 → 验证

| 阶段 | 必须回答 | 默认全量 | 按需（用户点名） |
|------|----------|----------|------------------|
| **规划** | 这份 PDF 有什么、该提什么 | `scan` + `adapt-plan` + `plan_amend`（G_plan） | 点名项即剧本；仍用格式/行业定位。不强制 plan_amend |
| **提取** | 值从哪一页哪段来 | convert → extract-tables / close | 同缓存 `resolve --need` / `extract-needs`（须先有 quality.json） |
| **验证** | 能否给人/下游 | qa → review → deliver-check | FieldRecord：`found` **仅当** `quote_verified`；否则 ambiguous |

E0–E4 是全量路径的实现细节（见下表）。按需之后若改口深研：同一 `cache_id` 补 plan_amend → close → deliver，不重转 PDF。

## 设计原则：程序做确定的事，AI 专家把关判断

- **程序只做可机器回验的确定性工作（零幻觉）**：双轨转换、meta 地图、records、勾稽/数值存在性/quote 回验。**`found` 必须 quote 回验成功**；有值未回验 → `ambiguous`。
- **语义判断由 AI 以顶级投资专家身份把关**：plan_amend、type_promote、叙述终态、QA 仲裁、review。`not_disclosed` 须附披露范围证据或 needle 零命中扫描；`rule_limitation` 须 rationale≥8 字并引用 finding sample。
- **没落盘 = 阶段没发生**。同一 blocker 连续 2 次相同失败即换路或诚实终态，禁止空转。

## 阶段 × 门禁（E0–E4，默认全量）

| 阶段 | 必须回答 | 强制产物 | 门禁 |
|------|----------|----------|------|
| **E0 草稿** | 这份 PDF 有什么、底线必要集是什么 | `adapt_plan.json`（`amended=false`） | **G_draft**：有 `analysis_required`、三表在列 |
| **E1 规划** | 本份优先服务哪几张分析卡？原型？明确不做？ | `agent_tasks_done/plan_amend.json` 写回 `adapt_plan` | **G_plan**：`amended=true` 且 agent-apply 过 |
| **E2 执行** | 修订集是否提全、过 QA | tables / narratives / quality / coverage | auto-heal：promote → narrative-scan → qa → agent-apply → coverage → review |
| **E3 分析就绪** | 五张卡能否按索引消费 | `fields/*.json`、`derived/analysis_facts.json`、`analysis_index.json` | **G_facts**：COMMON 字段 found（已回验）或诚实终态 |
| **E4 交付** | 能否给 deepdive S2 | `deliver-check` ok | **G_deliver**：含 plan_amend / analysis_index / COMMON 静默或未回验 / 承重表未仲裁 degraded |

## 何时使用

**默认全量**：「把年报核心数据全量提取出来」「深入解读需要的数据都拿出来」。

**按需**：「从年报提取前十大股东和分红方案」「合同负债是多少（要页码+quote）」。

## 不要用本技能

| 用户说法 | 改用 |
|----------|------|
| 财报列表 / 最新年报 PDF 在哪 | 让用户提供 PDF 或公开直链（A 股可用巨潮资讯网 cninfo.com.cn） |
| 三表数字、关键指标（平台口径） | 用本技能全量提取；WinMale 平台用户另可用 wm-statements / wm-data |
| 十大流通股东快照（不要年报原文） | `wm-shareholder-structure` |
| 本地没有 PDF 且无法下载 | 让用户提供文件或公开直链 |

## 依赖与预期

- 转换阶段需 `docling`+`pymupdf`（约 1-2GB，Python 3.10+，实测 docling 2.120.2 / PyMuPDF 1.24.14）；`scan/locate/cache` 无需。**解释器选择**：优先 `WM_REPORT_PYTHON` 指定的解释器，未设置时用 PATH 上的 `python3`；执行与依赖安装须用**同一个**已装 docling/pymupdf 的解释器，勿用 managed venv。
- 转换为双轨混合：Docling FAST 全档（版面/叙述/无框线表）+ PyMuPDF `find_tables` 接管有框线页表格（零幻觉、带单元格 bbox）+ ACCURATE 精修无框线报表页（约 10-24 页）。300 页年报约 **6-12 分钟**——**建议后台运行**；`--accurate` 可全档 ACCURATE（约 30-35 分钟，最高精度档）；sha256 缓存幂等，二次提取秒级命中。
- darwin 上默认 CPU（`--device cpu`），规避 MPS 内核崩溃。
- 本地已有 docling 模型缓存时**默认离线运行**（自动设 HF_HUB_OFFLINE，避免 HuggingFace revision 在线检查在网络波动时卡死转换；需更新模型时 `unset HF_HUB_OFFLINE TRANSFORMERS_OFFLINE`）。

## 七步流程（必须按序，产物落缓存可审计）

脚本门面（路径按已安装 pack，下同）：

```bash
python3 <skills_root>/wm-report-extract/scripts/wm_report.py <subcommand>
```

### ① 获取 + 转换（fetch / convert）

```bash
# 经 WinMale 平台查链接并下载（symbol 模式，可选；未接平台请用 --pdf-url 直链）
python3 …/wm_report.py fetch --symbol 601633 --filing-type annual [--report-date 2025-12-31]
# 或直链 / 本地路径
python3 …/wm_report.py fetch --pdf-url https://…/report.pdf
python3 …/wm_report.py convert <pdf路径|cache_id>   # 建议后台：耗时 8-20 分钟
```

产物：`report.md`（每个 PDF 页起始处 `<!-- page:N -->` 标记，表格已转 markdown，文本 NFKC 归一化）、`pages.json`（含每页竖线/横线统计）、`fitz_tables.json`（fitz 轨道表格的页内顺序与 bbox）、`convert_meta.json`。缓存 `~/.cache/wm-report-extract/{sha12}/`。

表格来源双轨仲裁（convert 内自动）：有框线页（竖线网格 + fitz 检出 ≥3 行）用 PyMuPDF 表格（数值全部来自页面文本，零幻觉，带 bbox）；无框线/三线表页用 Docling，其中报表页（资产负债/利润/现金流量表）自动 ACCURATE 精修；同页文本相似的纯文本表保留 docling 版（语义结构更好，fitz 版去重抑制）。`meta.json` 的 `tables[].track` 标注来源；跨页续表类型只从本合并链链头继承（防类型传染），同类型多条独立物理链各自成表不混源拼接（canonical 给结构分最高链）。

### ② 内容理解 meta（scan）

```bash
python3 …/wm_report.py scan <cache_id> --summary
# 已接 WinMale 平台时可选拉行业（--refresh-industry 强制刷新）；未接平台则仅 PDF 词表
```

`meta.json` 是后续一切的依据：

- `industry_hint`：行业探测。已接 WinMale 平台且有 `symbol` 时可选拉申万行业作先验（`source=platform|platform_conflict|pdf`）；未接平台则仅 PDF 词表。低置信且无平台映射时 `industry=null`。
- `document_profile`：`market/script/accounting/convert_health/novelty` 画像；含 `industry_source`
- `filing_kind`：`annual` / `q1` / `semi` / `q3` / `quarter` / `prospectus`
- `chapters` 章节树（正文锚点→目录回退）/ `sections` 子节锚点（`from_toc:true` 需复核）
- `tables[]` 全表 schema：headers/单位/期间列/科目样本/续表合并（`continued`）/类型——**类型是提示，headers 才是证据**
- `priority` 优先指引：按 coverage-checklist 通用层+行业层分组给出入口（结构性三表 > 特异签名表 > 锚点区间 > 关键词）
- `anomalies[]` 异常与降级（异常不中断，是处置依据，见下表）

| code | 处置 |
|------|------|
| `convert_failed` / `encrypted` / `convert_missing` | blocker：告知用户，建议解密/`--ocr`/`--accurate` 重转 |
| `low_text_page` | 该页可能是扫描图：值需跨页复核，必要时 `--ocr` 重转 |
| `table_fragment` | 碎表：改用正文键值对提取或相邻表拼接 |
| `chapters_from_toc` | 章节 page 为印刷页码与物理页有偏移，定位优先 `sections`/`tables`（物理页） |
| `missing_chapter_anchors` | 章节/目录均未解析出：用 `sections` + `locate` 定位 |
| `kangxi_compat` | quote 为 NFKC 归一化文本，与 PDF 原字符可能不同形 |
| `garbled` / `long_table` / `header_noise` / `table_type_unknown` | 复核、分段读、忽略版式噪声、读表头确认类型 |

### ②½ 方案适配（adapt-plan）

```bash
python3 …/wm_report.py adapt-plan <cache_id> [--result <result-...>]
```

产物：`result-*/adapt_plan.json`（`amended=false` 草稿）。以**深入分析一家公司**为目的，程序生成 compact prior（三表底线 + COMMON 承重字段 + 七原型致命变量 semi + 地图校准），**不是**行业百科：

- `prototype` / `industry_depth`（`thin`=可探测无行业 hard 清单）
- `analysis_required[]`：`hard|semi|skip`；地图有表指针的类型必入并挂 `map_refs`
- Agent **必须**走 E1 `plan_amend` 审定后 `amended=true`，否则 `close` 停在 G_plan

可选：`--analysis-plan <00-analysis-plan.md>` 把三个问题升权对应字段，不删 A–I 底线（见 workflow）。

### ③ 全表 records 确定性预提取（extract-tables）——应提尽提的机制保证

```bash
python3 …/wm_report.py extract-tables <cache_id>          # → records.json（秒级）
python3 …/wm_report.py locate <cache_id> "存货" --records # 按科目行检索（含断词归一匹配）
```

`records.json`：每张表每个数据行 → `{table, page, type, row_label, label_norm, values[{value,period,header}], unit, headers}`。数百页年报产出数千条行级记录，**每条可溯源到表+页**。三表/摘要等已定型；续表自动继承类型；跨页续表已合并。

### ④ 结构化分表（materialize-tables）

```bash
python3 …/wm_report.py materialize-tables <cache_id> [--force]
```

产物：`result-{ts}/manifest.json + tables/*.json + gaps.json + promote_candidates.json`。Python 只做高置信定型；其余进 generic。表格数据必须优先消费分表文件。

### ⑤ Agent 定型晋升（type_promote）

读 `promote_candidates.json`（每张 generic 的 title/headers/前 8 行/`type_hint`/`filing_kind`），对照 coverage-checklist **分析意图** 决定是否晋升。只输出 `confidence=high` 的项：

```bash
python3 …/wm_report.py apply-promotions <cache_id> --file promotions.json [--result result-…]
```

- 按「这张表回答哪个分析问题」晋升，禁止写死品牌/公司名
- 混两类或低置信 → 保持 generic
- 季报不要硬升年报才有的组
- 同类型多张物理表：第一张用稳定 `table_id`，其余为 `{type}_p{page}_i{index}`，禁止静默合并

**规则化预晋升（0.6.1 起必跑，Agent 晋升的前置）**：行业 allowlist ∪ 跨业态邻接白名单
（hint 共现 ≥2，如煤电一体的 power_generation）内每 hint 取首个候选自动晋升，无总数上限：

```bash
python3 …/wm_report.py auto-promote <cache_id> [--result result-…]
```

### ⑤½ 叙述证据扫描（narrative-scan，0.6.1 起）

```bash
python3 …/wm_report.py narrative-scan <cache_id> [--result result-…]
```

- 通用 MD&A 4 项 + 各行业叙述/required_gaps 的 needles（`domain/narratives.py` 声明式）
- needle 命中 → 自动 `found`（quote+page，过 review 硬门回验）；未命中 → `agent_tasks/`
  证据包（章节区间/页码/excerpt/needles）——**程序不判 not_disclosed，留 Agent 终审**

### ⑤¾ Agent 闭环（agent_tasks 协议，0.6.1 起）

对 `agent_tasks/*.json` 的待办，Agent 读证据包后写 `agent_tasks_done/*.json`：

| 任务 | 输出 | 机器校验 |
|------|------|----------|
| `plan_amend`（E1 审定剧本） | `amendments[]`：upgrade/skip/add/reprototype/wont_do | why≥8 字；地图有表禁止 skip；三表 hard 禁止 skip；写回 `amended=true` |
| `narrative_close`（叙述/gap 终态） | `found`（quote+page）/ `not_disclosed`（reason≥8字）/ `not_found` | quote 逐字在 report.md 且页码一致 |
| `qa_adjudication`（勾稽仲裁） | `rule_limitation`（附 rationale，标注保留不删）/ `real` | finding 必须存在于 quality.json；close 内 qa 后 apply，确定性规则可先自动仲裁 |
| `industry_confirm`（行业确认） | 目录内 industry | industry 必须在 INDUSTRY_HINTS；有平台申万未映射时扩 `domain/sw_industry_map.py`（adaptation），否则按 PDF 词表确认 |

```bash
python3 …/wm_report.py agent-apply <cache_id> [--result result-…]   # 校验不过即拒（exit 1）
```

### ⑥ 质量门（qa-tables，给下游前必跑）

```bash
python3 …/wm_report.py qa-tables <cache_id> [--result result-…] [--verdicts qa-verdicts.json]
```

- Python：列错位、缺单位、垃圾表头
- Python v2 质量门（对照 PDF 原文）：
  - **勾稽校验**：资产=负债+权益恒等、合计=Σ分项（减:项为负、其中:项跳过）、期初+增减=期末、同比%用金额重算——失败记 `identity/subtotal/roll/yoy_mismatch`（degraded，不删行）
  - **数值存在性**：表内每个数字必须真实出现在溯源页 PDF 文本（`value_not_on_page`；超 30% 整表 demote）
  - **quote 回验**：行 quote 逐字（NFKC 归一化）存在于溯源页（`quote_unverified`）
- Agent：语义复核 typed 表（会议议程冒充激励表、利润变动原因冒充海外经营等）→ `demote` 或 `split`
- 产物 `quality.json`；**无此文件或未跑 QA，禁止把 typed 表交给分析角色**
- `status=fail` 表示发生过 `demote`/`split`；下游仍只消费 `verdict=pass` 的 typed 表；suspect 数值/quote 进 `gaps.json` 供复核

### ⑥½ 独立审核（review-extract）

```bash
python3 …/wm_report.py review-extract <cache_id> [--result <result-...>]
```

- 审核与提取角色分离：**审核不改表，只读产物打分**
- 硬门：`quality.json` 存在、叙述 `found` 必须有 quote+page、`required_gaps` 必须终态、quote 可回验、画像一致性、**年报/半年报三表定型**（`statement_signature_gap`）
- 软门：一季报/三季报三表缺一、demote/split、未 promote 的非噪声 `type_hint`
- QA：三表行标签须命中科目词；假利润表（公司名当 item）→ demote
- novelty / hard fail 时写 `derived/evolution_proposal.json`（含 `actions`、`missing_type_signatures`、`noise_type_hints`）；**只产 proposal，不自动改规则库**

### ⑥¾ HTML 阅览（render-html，可选，非必跑）

```bash
python3 …/wm_report.py render-html <cache_id> [--result result-...] [--out report.html]
```

- 产物默认：`result-*/report.html`（单文件自包含，系统字体，可离线打开）
- 若有 `coverage.json`，首屏展示四态质量看板（高/低/应提未提/应提未披露）；无 HTML 也可凭 coverage 验收
- **只嵌入 `quality.json` 中 `verdict=pass` 的表** + gaps / review / QA findings；只读，不在页面改数；typed 表展示 `variant` 徽标（primary/parent_company/summary/analysis/supplementary）
- 侧栏按覆盖组导航；三表切换；行点击展开 quote+页码抽屉

### ⑥⅞ 一键收口（close，auto-heal）

```bash
python3 …/wm_report.py close <cache_id> [--result result-...]
```

0) **G_plan**：无 `amended` adapt_plan → 写 `agent_tasks/plan_amend.json` → todo → **exit 1**，禁止 auto-promote 交差
1–6) auto-promote → narrative-scan → qa-tables → agent-apply → coverage → review（现有）
7) 投影 COMMON 字段 + `analysis_facts.json` / `analysis_index.json`
8) 内部 `deliver-check`；fail → `todo_tasks` 含 `deliver:*`

Agent 落地循环：**只做 todo → agent-apply → 再 close**。`--no-plan-gate` 仅测试/排障，交付禁用。

> 质量门不可取消。给下游前再跑 **`deliver-check`**（只读；HTML 非权威）。

### ⑦ 个性化增量提取（核心包之外的清单外需求）

核心必要集已在①–⑥⅞ 全量落地（应提尽提）。coverage-checklist 固定覆盖之外、定型表够不到的个性化需求走**增量抽取**：

```bash
python3 …/wm_report.py resolve <cache_id> --need "合同负债" --need "存货" --write-fields
```

产物（L2 首选）：`result-{ts}/fields/<field_id>.json` + `result-{ts}/fields/_batch.json`，并回填 `result-{ts}/manifest.json -> catalog.fields[]`（提供可枚举的 FieldRecord 证据索引；每个数值带页码与 quote，可复核）。**0.6.0 起港股 IFRS 三大报表已可定型（简繁签名）；非报表港式表仍可空，convert + resolve 照跑。**

L2 传统备选（legacy）：`extract-query` 仍可用，但它把 `value` 留空给 Agent（禁止写入 PDF 之外数字），用于需要更复杂“切片级”语义时。

第三方（东财/现货网站）数字 **不得** 写入 adhoc.json——PDF 没有就是 `not_in_pdf`；研究包用 L3 Web 另记。

## 输出形态

- **权威交付包（给 Agent / 下游分析）**：`adapt_plan.json`（`amended=true`）+ **`coverage.json`** + `quality.json` + `review.json` + `analysis_index.json` + 仅 `verdict=pass` 的 `tables/*.json` + `narratives/*.json` + `fields/*.json` + `gaps.json` + `manifest.json`。
- **交付前必跑**：`wm_report.py deliver-check`。分析 Agent **只读 `analysis_index.json`** 拉齐五张卡，不得把未索引 typed 表当作已服务分析卡。
- **HTML 非权威**：`render-html` 仅可选阅览；**不得**以 HTML 代替 coverage/review 验收；缺 HTML 不影响 `purpose_ok`。
- 给人：正文结论 + 关键数字表（每行带页码角标）+ 来源 footer；需要看板时再开 HTML。

## 禁止

- 无 `quality.json` / 未经 `plan_amend` / 无 `analysis_index.json` / COMMON 字段静默或未回验 / 承重表未仲裁 degraded / `deliver-check` 未过就把产物交给下游分析。
- 用「HTML 看起来全了」代替 `coverage.purpose_ok` 与 `review.status=pass`。
- 把 Python `type_hint` 或未晋升的 generic 当成稳定 `table_id`。
- 全量提取时跳过 D_mda / C_segments，或把变动原因表只抽成金额。
- 把具体公司品牌名、口号写进 plan 或覆盖清单。
- 编造数值/页码；quote 必须逐字（NFKC 归一化后）来自该页；有值未回验不得标 `found`。
- 用第三方数据源（东财/同花顺等）补 PDF 里没有的数——not_found 就是 not_found；不得写入 adhoc.json。
- macOS 上用 `--device mps`（Metal 内核崩溃）；默认 cpu。
- 港股报告：0.6.0 起三大报表签名/章节锚/行业词已简繁适配；仍定不出的表（港式非报表版式）**不要跳过 convert / locate / resolve**，改走 L2 个性化抽取。美股/英文报告：锚点库未适配，同样走 L2。

## 深入参考

| 需要 | 读 |
|------|----|
| 分析卡 / 七原型 briefing（E1 必读） | [references/analysis-needs.md](references/analysis-needs.md) |
| 四步操作细节与故障排查 | [references/workflow.md](references/workflow.md) |
| 溯源契约、缺口复盘、derived 规则 | [references/provenance.md](references/provenance.md) |
| 全量提取覆盖清单 | [references/coverage-checklist.md](references/coverage-checklist.md) |
| 锚点/表格签名模式库（扩展指南） | [references/anchors.md](references/anchors.md) |
| 规则演进/新行业适配提案流程 | [references/adaptation.md](references/adaptation.md) |
| 请求/响应示例 | [examples/](examples/) |
