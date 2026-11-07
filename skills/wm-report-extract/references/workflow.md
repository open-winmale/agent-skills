# 操作手册

SKILL.md 的展开版。脚本门面：`python3 .cursor/skills/wm-report-extract/scripts/wm_report.py`（下称 `wm_report.py`）。

> **目标定位**：默认产出**全量核心信息包** + **分析就绪索引**；用户点名数据项时走 `resolve` / `extract-needs` 按需路径（须先有 `quality.json`）。分工：转换/meta/records/质量门/字段投影归 Python；**plan_amend**、type_promote、narrative 终态、qa_adjudication、industry_confirm、review 由 AI 完成且必须可复核。`found` 必须 quote 回验。E0–E4 门禁不过不得进入下一阶段。
## E0 / E1 方案草稿与动态规划

### E0 程序草稿（adapt-plan）

```bash
wm_report.py adapt-plan <cache_id> [--result result-...]
```

- 产物：`result-*/adapt_plan.json`（`amended=false`；含 `prototype` / `industry_depth` / `analysis_required`+`map_refs` / `strategy`）
- compact prior：三表底线 + COMMON 承重字段 + 七原型致命变量（semi）+ 地图校准。**不要**为每个 industry 复制 fossil 级硬清单。
- 数据地图校准：模板未列但地图有的类型不得静默漏提
- `q1/q3` → 完整 MD&A / 致辞 `not_applicable`；原型 F 跳过合同负债/应收/存货
- thin 行业（钢/化/通信/互联网/农业/半导体/通用制造）：可探测、无行业 hard；`purpose_ok` 不得解释为行业深研已齐

### E1 Agent plan_amend（G_plan）

写 `agent_tasks_done/plan_amend.json` 后 `agent-apply`。必读：`adapt_plan.json` + `references/analysis-needs.md` 对应原型节。

```json
{
  "task": "plan_amend",
  "id": "plan_amend",
  "prototype": "A",
  "amendments": [
    {"op": "upgrade", "id": "power_generation", "why": "地图与正文均有发电量表",
     "evidence": {"map_ref": {"kind": "table", "page": 33}}},
    {"op": "skip", "id": "installed_capacity", "why": "无装机容量专用披露",
     "evidence": {"filing_kind": "annual"}}
  ]
}
```

- `upgrade` / `skip` / `add` / `reprototype` / `wont_do`；why≥8 字
- **地图有表指针禁止 skip**；三表 hard 禁止 skip；`wont_do` 不能覆盖 hard+map_rescued
- `close` 若 `amended≠true`：写 `agent_tasks/plan_amend.json` → todo → exit 1，禁止 auto-promote 交差
- 落地循环：只做 todo → agent-apply → 再 close；同一 blocker 连续 2 次相同失败则换路或 `not_disclosed`

records 优先、同义词、异常转化、C/D 组映射纪律仍适用（见执行提取节）。

## ① 获取 + 转换

### 输入三选一

```bash
# A. symbol（经 wm-filings，需 wm-skillhub 已安装；自动选最新或指定报告期）
wm_report.py fetch --symbol 600036 --filing-type annual --report-date 2024-12-31

# B. PDF 直链
wm_report.py fetch --pdf-url https://static.cninfo.com.cn/…/gsgb2024n.pdf --title "XX 2024 年报"

# C. 本地路径（仅导入不转换 / 直接转换）
wm_report.py convert /path/to/report.pdf [--accurate] [--ocr] [--force]
```

- `fetch --convert` 一步到位；转换**建议后台运行**（300 页约 8-20 分钟）。
- `--accurate`：ACCURATE 表格模式，慢 2-3 倍但对复杂表格更准；默认 FAST 已够用于常规提取。
- `--ocr`：仅扫描版（`low_text_page` 异常大面积出现时）。
- 产物与缓存：`~/.cache/wm-report-extract/{sha12}/`（`WM_REPORT_CACHE_DIR` 可覆盖）。幂等：重复 convert 直接命中缓存；`--force` 重转。
- **并行 fetch 勿同时下载多份报告**；脚本已用 uuid 临时文件 + 页数校验（季报 ≤80 页、年报 ≥50 页）防竞态错文件。

### 转换产物

| 文件 | 内容 |
|------|------|
| `report.md` | 正文，每 PDF 页起始 `<!-- page:N -->`；表格为 markdown；文本 NFKC 归一化（康熙部首→常规字）；页眉页脚已剔除 |
| `pages.json` | 每页行号区间、字符数、标题、表格数、页眉页脚命中 |
| `convert_meta.json` | 耗时/模式/docling 版本/PDF 书签/加密状态/异常页清单 |

## ② 扫描 meta

```bash
wm_report.py scan <cache_id>            # 生成/命中 meta.json
wm_report.py scan <cache_id> --summary  # 紧凑摘要（Agent 必读）
```

`meta.json` 字段速查：

- `industry_hint`：`{industry, confidence, matched[, transport_segment]}`——bank/insurance/broker/real_estate/automobile/energy/manufacturing/nonferrous/**pharma/consumer/transport_infrastructure/fossil_energy** 特征词打分；**标题含「汽车」「矿业」「证券」「保险」「电力」「地产」「制药」「酒业」「高速」「港口」「煤业」「石油」等加权**，短文档（<50 页）降低 bank 词权重，防季报误判；冲突仲裁见 `domain/policy.py`（含 pharma/consumer/fossil 压 manufacturing、fossil↔energy↔nonferrous、交运压地产等）。交运行业额外写 `transport_segment=highway|port|mixed`。
- `document_profile`：`{market, script, accounting, filing_kind, convert_health, novelty, novelty_reasons}`——统一给适配/审核使用。
- `filing_kind`：`annual` / `q1` / `semi` / `q3` / `quarter` / `prospectus`——驱动 MD&A 叙述清单（`q1/q3` 标 not_applicable）。
- `chapters[]`：`{num,title,anchor,page,page_end,line,source}`——`source:"toc"` 时 page 为**印刷页码**。
- `sections[]`：子节锚点；`from_toc:true` = 仅目录命中，**定位需 locate 复核**。
- `tables[]`：全表 schema——`{index,page,line,line_end,rows,cols,type,type_hint,headers,unit,periods,sample_labels,continued,continued_by,quality}`；`type` 仅高置信；`type_hint` 供 Agent 晋升，不当终裁。
- `section_summaries[]`：锚点页区间内的表格分布。
- `priority[]`：checklist 分组 → 入口（结构性三表 high > 特异签名表 medium > 锚点 medium/low > keyword）。
- `pages[]` / `anomalies[]`：页面画像；异常处置表见 SKILL.md。

## ③ 全表 records 预提取

```bash
wm_report.py extract-tables <cache_id> [--force]   # → records.json，秒级
wm_report.py locate <cache_id> "存货" --records     # 行科目检索（断词归一：'股 东'==‘股东'）
wm_report.py resolve <cache_id> --need "合同负债" --need "存货" [--write-fields]
# → result-{ts}/fields/<field_id>.json（可枚举的 FieldRecord 证据索引）；港股 typed 表可空仍要跑
```

- 每条 record：`{table,page,type,row_label,label_norm,values[{value,period,header}],unit,headers}`。
- 检索优先用 `label_norm`（去空白）；docling 会把跨行科目断成「归属于上市公司股 东的净资产」。
- 纯文本行（无数值）已被过滤；续片类型继承头表。
- **resolve**：L1 typed 表（quality=pass）→ records（确定性 value 填充）→ 正文 locate（quote 回验）；`status=found|not_found|ambiguous`；输出 FieldRecord，并可在 `result-{ts}/manifest.json -> catalog.fields[]` 中被外界枚举复用。

（遗留备选）**extract-query**：先 records 再正文 locate；把 `value` 留空给 Agent（禁止把 PDF 外数字写入）；适用于更复杂的切片级“半结构语义”场景。

## ④ 结构化分表（materialize-tables）

```bash
wm_report.py materialize-tables <cache_id> [--force] [--out result-20260818T120000Z]
```

- 输入：`records.json` + `meta.json`
- 输出：`result-{ts}/manifest.json`、`tables/*.json`、`gaps.json`、`promote_candidates.json`
- 分表使用列位置与 `meta.tables[].periods` 映射；`variance_reasons` 按表头名映射本期/上年/变动/原因，禁止把占比列当上年金额
- 对 `type is None` 且 `rows >= 3` 的表生成 `generic_table_*`，并写入 `promote_candidates.json` 供 Agent 晋升

## ④b Agent 定型晋升 + 质量门

```bash
# Agent 读取 promote_candidates.json，按 checklist 意图输出 promotions.json（仅 confidence=high）
wm_report.py apply-promotions <cache_id> --file promotions.json [--result result-…]

# 必跑。--verdicts 为 Agent 语义复核（demote/split/pass）
wm_report.py qa-tables <cache_id> [--result result-…] [--verdicts qa-verdicts.json]
```

- 晋升约束：混两类不晋升；低置信保持 generic；禁止写死品牌/公司。同类型多表用独立 `table_id`，禁止静默合并。
- QA：Python 查列错位/缺单位；Agent 查语义污染。`demote` 整表退回 generic；`split` 只保留匹配行、其余回 generic。
- `quality.json` 的 `status=fail` 表示发生过 demote/split；无此文件不得给分析角色。下游只消费 `verdict=pass` 的 typed 表。

## ⑤ 执行纪律（E1 已审定后）

1. **records 优先**：先 `locate --records` 行检索（含同义词），命中即 `record_map`；正文型才 `text_scan`。
2. **同义词表**：股东权益合计/所有者权益合计、年末/期末现金及现金等价物余额、净减少额/净增加额、资产合计(银行版)/资产总计、归属于母公司股东/归属于上市公司股东。
3. **异常转化**：`anomalies` 逐条映射为 `anomaly_strategy`，受影响字段的 `fallback` 必填。
4. **泛化**：不硬编码页码；不把公司品牌名写入 plan。换一份财报 plan 重新生成。
5. `sections.*.from_toc=true` 的锚点：`locate` 确认正文页后再定区间。
6. **C/D 组映射纪律**：
   - `record_map` 覆盖全部 `type=segments` / `production_sales` 数据行。
   - `type=variance_reasons` → `{value, yoy_pct, reason}`，reason 列缺失时仅对该行做 `text_scan` fallback；仍无命中则写入 `gaps.json`。
   - `type=mda_ratios` → 毛利率与期间费用占营收比。
   - `mda_business` / `mda_industry` / `mda_outlook` / `risk_factors` / `chairman_letter` → `text_scan` 对应锚点页。

剧本结构与修订协议见文首 **E0 / E1**，禁止再维护第二套 plan JSON。

## ⑥ 执行提取

- 读 `report.md` 的 plan 指定行区间（`pages.json` 换算页→行）。
- 对 `manifest.catalog.tables` 中已有表直接引用；仅对 `narratives` 执行 `text_scan`。
- 叙述输出写 `result-{ts}/narratives/*.json`，并回填 `manifest.catalog.narratives`。
- **缺口复盘**：`status=not_found` 的字段，换 `fallback` 方法或 `locate` 新锚点重扫一轮再定论。
- 超长表分段读（`long_table`），跨页行看下一页页标记前的连续表格块。

## ⑥½ 审核（review-extract）

```bash
wm_report.py review-extract <cache_id> [--result result-...]
```

- 审核与提取角色分离：**只读产物，不改表**
- 硬门：`quality.json`、叙述 quote+page、`required_gaps` 终态、quote 回验、画像一致性、年报/半年报三表
- 软门：q1/q3 三表缺一、demote/split、未 promote 的非噪声 `type_hint`
- novelty / hard fail 写 `derived/evolution_proposal.json`（`actions` + 正文未匹配签名）；写回须 `validate + 样本 + 批准`

## ⑥¾ HTML 阅览（render-html）

```bash
wm_report.py render-html <cache_id> [--result result-...] [--out report.html]
```

- 默认写出 `result-*/report.html`：Hero（quality/review 徽章）+ 侧栏导航 + 三表/经营表 + 审核 gaps
- 仅 `verdict=pass` 表进入主栏；demote 表不展示
- 只读；修复走 `close`（auto-heal：auto-promote → narrative-scan → qa → agent-apply → review）后再重跑本命令

### auto-heal（0.6.1 已实现：`close` 命令）

目标：减少按公司手写 `eval/close_*.py`，**不取消质量门、不放宽 review 硬门**。

```text
close <cache_id> --result …
  0) G_plan：无 amended adapt_plan → 写 agent_tasks/plan_amend.json → todo → 停止
  1) auto-promote：行业 allowlist + 跨业态邻接（hint 共现≥2）每 hint 取首候选
  2) narrative-scan：叙述 needles 命中→found；未命中→agent_tasks（必附 map_refs/promote_candidates）
  3) qa-tables：确定性 demote / degraded；合并旧 adjudicated；auto_adjudicate 已知误报
  4) agent-apply：应用 agent_tasks_done/*.json（含 plan_amend；quote 逐字校验 / qa_adjudication，不过即拒）
  5) 写出 coverage.json（四态；地图有表指针未提取→missing_extract）
  6) review-extract；投影 analysis_facts + analysis_index
  7) deliver-check；fail → todo_tasks 含 deliver:*
```

agent_tasks 协议（Agent 判断的输入/输出/机器校验）：

- **先读数据地图**：`map_refs` + `promote_candidates` + `adapt_plan.analysis_required`，再定论
- `plan_amend`：见文首 E1
- `narrative_close`：found 须 quote+page（quote 逐字在 report.md 且页码一致）；
  not_disclosed 须 reason ≥8 字（引用披露范围证据）
- `type_promote`：hard 且地图有表指针、未定型时生成 `promote-{id}.json`
- `qa_adjudication`：degraded 勾稽发现逐条裁定 rule_limitation（标注保留不删）或 real
- `industry_confirm`：目录内行业确认（目录外走 adaptation.md 提案流程）

禁止：静默改数字；无 quote 的 found；跳过 `quality.json`；无视地图表指针空转 not_disclosed。

**HTML「需复核」**：仅未仲裁或 `adjudicated=real` 的 degraded 打行级黄标；`rule_limitation` 只在 finding 区显示「已仲裁」。
## ⑦ 交付验收（deliver-check）

`close` 收口之后、把产物交给下游分析之前，**必跑**只读门禁（不改数、不跑 promote/qa、不写 HTML）：

```bash
wm_report.py deliver-check <cache_id> [--result result-...]
# ok=false → exit 1；输出 {ok, blockers[], warnings[]}
```

### 阻断（blockers → 不可交付）

| 条件 | 说明 |
|------|------|
| 无 `quality.json` | 未过 QA，typed 表不得给下游 |
| 无 `review.json` 或 `status≠pass` | 独立审核未过；含 `hard_failures` |
| 无 `coverage.json` 或 `purpose_ok≠true` | 深研目的未达成 |
| `hard_missing_extract` 非空 | 任一 hard 项仍为 `missing_extract` |
| coverage 声称已提但无 `verdict=pass` 定型表 | 权威与质量门不一致 |
| `adapt_plan.amended` 非 true | 未经 E1 plan_amend |
| 无 `analysis_index.json` | 分析侧无法按五张卡消费 |
| COMMON 字段静默缺失 | 无 FieldRecord 且无诚实终态 |

权威交付包：`adapt_plan.json`（amended）+ `coverage.json` + `quality.json` + `review.json` + `analysis_index.json` + `verdict=pass` 的 `tables/*.json` + `narratives/*.json` + `fields/*.json` + `gaps.json`。

### 允许（不阻断，记 warnings）

- `not_disclosed` / `not_applicable`（诚实终态）
- `semi` 的 `missing_extract`（非 hard）
- 残留 `agent_tasks/*.json` 待办（非 hard 阻断项时）
- 缺 `report.html`（HTML **非权威**）

### HTML（可选，非验收物）

- 仅在 `deliver-check` **ok** 之后可选 `render-html`
- **禁止**用「看 HTML 过了」代替 coverage/review；HTML 只嵌 `verdict=pass` 表，缺页不影响 `purpose_ok`

## 常见故障

| 症状 | 处置 |
|------|------|
| `docling` ImportError | `pip install docling pymupdf`（Python 3.10+） |
| fetch 鉴权失败 | wm-skillhub 未安装/未登录：改用 `--pdf-url` 或本地路径 |
| 转换超慢 | 正常（首轮模型加载+逐页）；确认 FAST 模式与 8 线程；勿重复 convert（有缓存） |
| `convert_failed` | 看 convert_meta.error；扫描版试 `--ocr --force` |
| MPS 崩溃（darwin） | 保持默认 `--device cpu`，勿用 mps |
