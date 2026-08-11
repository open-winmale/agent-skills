---
name: wm-discover
display_name: "统一发现"
version: 1.4.1
description: 用自然语言找公司/证券代码、行业与指数、SkillHub 技能、指标定义、XS 函数(vfunc，含 example_call_xs/call_spec 与域库 kline|notice|filings…；稳定域库已随 init 预载)/测试示例、选股字段。不确定 wm-* 时先 discover（domain=skill），再 wm.sh run。
---

# 统一发现

**SkillHub 路由入口。** 不知道该调哪个官方技能时，先本接口（默认含 **`skill`**），读 `domain=skill` 的 `id`，再 **`wm.sh run`**。

也用于：**公司名→证券代码**、行业/指数、指标定义/公式、XS 函数签名（含 **example_call_xs / call_spec**；`require` 可忽略）与 tests 示例、域库 API（`notice.*` / `filings.*` / `kline.*` 等）、选股字段。

本 Pack **不能** `skills/run` / `wm.sh run wm-discover`。

## 会话缓存与高频 Fast-Path 映射（免重复 discover）

若在同一次 Session 内已通过以下自然语言映射定位到对应 Skill，**无需重复发起 discover**，直接调用对应 Skill：
- 「代码 / 现价 / 摸底 / 一页纸 / 行情」 → `wm-company-card`
- 「生意模式 / 靠什么赚钱 / 业务」 → `wm-company-business`
- 「贵不贵 / 估值 / PE / PB / 市赚率」 → `wm-valuation`
- 「负债 / 债务风险 / 杠杆 / 爆雷」 → `wm-debt-safety`
- 「现金流 / 利润含金量 / 纸面利润」 → `wm-cashflow-quality`
- 「分红 / 股息率 / 派息」 → `wm-dividend-quality`
- 「公告 / 减持 / 回购 / 事件」 → `wm-notice-radar`
- 「选股 / 条件筛 / 选股票」 → `wm-screen-index`
- 「GDP / CPI / PMI / M2 / 社零 / 宏观数据」 → `wm-data`（`action=macro`）
- 「沪深300 / 指数点位 / 指数成分」 → `wm-index`（讲「今天涨跌」须看 `quote_status=live_ok`）
- 「白酒行业 / 行业中枢 / 行业成分」 → `wm-industry`（批量码→名用 `action=resolve`）
- 「涨跌家数 / 今日盘面 / 分板块涨跌 / 市场广度」 → `wm-analysis-nav` `theme=market` → `wm-analysis-run`（勿新 L1、勿手搓 XS）
- 「财务分析页 / 研读包」 → `wm-analysis-nav` `theme=research` → `wm-analysis-run`

## 对人

- 「有没有查股息 / 财报 / 公告的能力」→ 找对应 SkillHub 技能
- **公司名 / 简称 / 代码 → 证券代码**（`domain=symbol`，默认已开）
- 行业 / 指数名、别名、代号 → `industry.*` / `index.*`
- 财务/估值指标名 → `$` 指标（含 definition / formula）
- 「RANGE / AR / 年同比怎么写」→ `vfunc` 静态索引
- 「公告 / 年报 / K 线库函数怎么调」→ `vfunc`（读 `example_call_xs`；稳定域库已预载，见 `wm-xs/references/domain-libs.md`）
- 选股条件里的字段或枚举取值 → `domain=screener`

## 对 Agent

### 硬规则（技能路由）

1. 用户意图像「查股息、分红、财报/年报、公告、负债、现金流、估值、自选、回测…」而你**不确定 skill id** → **必须先** `$WM discover`，`q` 用用户原话或关键词，**保留默认 domains（含 `skill`）** 或显式 `domains:["skill"]`。
2. 命中 `hits[].domain == "skill"` → 取 `id` → **`$WM run <id>`**，不要改用公告/裸 XS/第三方硬凑。
3. 中文支持子串：`q=历史股息` 可命中「股息与分红」；`q=年报 PDF` 可命中「财报检索」。
4. 仅当 skill 域无合适命中，才降级到 metric / vfunc / xs-eval。
5. **`vfunc` 域库**（`kline.*` / `notice.*` …）：读 `example_call_xs` + `call_spec`（`require` 可忽略）；有 `prefer_skill` 且用户只要产品结果 → 先 `$WM run` 该 L1。

### 何时用

| 需要 | domains / 说明 |
|------|----------------|
| **该用哪个官方技能** | **`skill`** |
| **公司名 / 证券代码** | **`symbol`**（默认已含） |
| 行业（申万等） | **`industry`** → `industry.S34`（默认已含） |
| 指数 | **`index`** → `index.hs300`（默认已含） |
| 分析用 `$` 指标定义/公式/示例调用 | **`metric`**（默认已含） |
| XS 函数签名 / 返回形状 / 示例调用 / 测试示例 | **`vfunc`**（默认已含；别名 `fn`） |
| 域库 API（公告/财报/K线/股息/分部…） | **`vfunc`** + 命中字段 `require` / `prefer_skill` |
| 选股索引字段/枚举 | **`screener`** |
| 策略卡 | `strategy` |
| 平台树全文 ripgrep | 显式 `scripts` + scope（深挖；默认不要） |

默认 domains：`symbol|metric|strategy|skill|screener|vfunc|index|industry`。

一次命中尽量带齐下一步：`id` / `require` / `example_call_xs` / `call_spec` / `prefer_skill` / `related`。

选股 `screener` 搜名时：后端对增速族做同义扩展；未提「行业」时公司字段优先于 `$CUR_IND_*`。仍无命中 → 换词再搜；仍无 → `wm-screen-index` / 分析师 + `wm-xs`（**禁止**第三方选股）。

### 何时不要用

- 已明确 skill id 且只要 run → 直接 `$WM run`
- 已有代码且只要行情/财务卡 → 直接对应 L1
- **执行选股筛池** → `wm-screen-index` `action=conditions`
- 写短 XS → `wm-xs`（先用本接口对齐 `$` / 函数名与 **require**）

### 调用

```bash
WM="bash .cursor/skills/wm-skillhub/scripts/wm.sh"
# 发现技能（优先）
$WM discover '{"q":"历史股息","domains":["skill"],"market":"cn","limit":10}' --result
# 指标定义
$WM discover '{"q":"ROE","domains":["metric"],"market":"cn","limit":10}' --result
# 公司 / 证券代码
$WM discover '{"q":"贵州茅台","domains":["symbol"],"market":"cn","limit":5}' --result
# 行业 / 指数
$WM discover '{"q":"白酒","domains":["industry"],"limit":5}' --result
$WM discover '{"q":"沪深300","domains":["index"],"limit":5}' --result
# 函数 / 域库（读 require + example_call_xs）
$WM discover '{"q":"kline.query_bars","domains":["vfunc"],"limit":5}' --result
$WM discover '{"q":"公告 减持","domains":["vfunc"],"limit":10}' --result
# 选股字段
$WM discover '{"q":"湖南","domains":["screener"],"scopes":["name","code","content"],"market":"cn","limit":20}' --result
```

| domain | 说明 |
|--------|------|
| **`skill`** | SkillHub 官方技能 |
| **`symbol`** | 公司 / 证券代码 |
| **`index`** | 指数：`id=index.hs300` + `example_call_xs` + `related` |
| **`industry`** | 行业：`id=industry.S34` + `example_call_xs` + `related` |
| `metric` | `$` 指标；`definition` / `formula` / `example_call_xs` |
| **`vfunc`** | 内核/host 函数 + **脚本域库**（`require`/`lib`/`prefer_skill`）+ tests/smoke 示例 |
| `screener` | 选股索引（需 `user:screener:indicator:read`） |
| `strategy` | 策略卡 |
| `workspace` / `scripts` | 用户文件 / 平台脚本树全文（scripts 需额外 scope） |

### 如何读结果

- `hits[]`：`domain` / `id` / `title` / `snippet` / `matched_fields`
- **`domain=skill`**：`id`=`wm-*` → **`$WM run`**（禁止手搓 HTTP；禁止对本 Pack `run`）
- **`domain=symbol`**：`id`=证券代码 → 公司卡等 L1（`$WM run`）
- **`domain=index|industry`**：直接用 `id` 写 XS；`related` 可 `$WM run`
- **`domain=metric`**：`definition` / `formula` / `example_call_xs`
- **`domain=vfunc`（域库）**：`example_call_xs` + `call_spec` → `$WM xs-eval`（稳定域库已预载，`require` 可忽略）；有 `prefer_skill` 且只要产品结果 → 先 L1。细则：`wm-xs/references/domain-libs.md`

### 失败与边界

- 0 hits：换词再搜；仍无 → 说明未覆盖，**禁止 invent**
- `SKILL_NOT_RUNNABLE`：你对本 Pack 误用了 `run` → 改用 `$WM discover`
- 选股执行不在本接口 → `wm-screen-index`
