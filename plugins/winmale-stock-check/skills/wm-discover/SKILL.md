---
name: wm-discover
display_name: "统一发现"
version: 1.3.3
description: 用自然语言找公司/证券代码、行业与指数、SkillHub 技能、指标定义、XS 函数(vfunc，含 call_spec/returns_shape/ex 与域库 notice|filings|kline…)/测试示例、选股字段。不确定 wm-* 时先 discover（domain=skill），再 skills/run。
---

# 统一发现

**SkillHub 路由入口。** 不知道该调哪个官方技能时，先本接口（默认含 **`skill`**），读 `domain=skill` 的 `id`，再 `POST /v1/skills/{id}/run`。

也用于：**公司名→证券代码**、行业/指数（`industry.S34` / `index.hs300`）、指标定义/公式、XS 函数签名（含 **call_spec / returns_shape / ex**）与 tests 示例、域库 API（`notice.*` / `filings.*` / `kline.*` 等）、选股字段。

## 对人

- 「有没有查股息 / 财报 / 公告的能力」→ 找对应 SkillHub 技能
- **公司名 / 简称 / 代码 → 证券代码**（`domain=symbol`，默认已开）
- 行业 / 指数名、别名、代号 → `industry.*` / `index.*`
- 财务/估值指标名 → `$` 指标（含 definition / formula）
- 「RANGE / AR / 年同比怎么写」→ `vfunc` 静态索引
- 「公告 / 年报 / K 线库函数怎么调」→ `vfunc`（`notice.*` / `filings.*` / `kline.*`…）
- 选股条件里的字段或枚举取值 → `domain=screener`

## 对 Agent

### 硬规则（技能路由）

1. 用户意图像「查股息、分红、财报/年报、公告、负债、现金流、估值、自选、回测…」而你**不确定 skill id** → **必须先** `POST /v1/analysis/xs/discover`，`q` 用用户原话或关键词，**保留默认 domains（含 `skill`）** 或显式 `domains:["skill"]`。
2. 命中 `hits[].domain == "skill"` → 取 `id` → **`skills/run`**，不要改用公告/裸 XS 硬凑。
3. 中文支持子串：`q=历史股息` 可命中「股息与分红」；`q=年报 PDF` 可命中「财报检索」。
4. 仅当 skill 域无合适命中，才降级到 metric / vfunc / notice / xs-eval。

### 何时用

| 需要 | domains / 说明 |
|------|----------------|
| **该用哪个官方技能** | **`skill`** |
| **公司名 / 证券代码** | **`symbol`**（默认已含） |
| 行业（申万等） | **`industry`** → `industry.S34`（默认已含） |
| 指数 | **`index`** → `index.hs300`（默认已含） |
| 分析用 `$` 指标定义/公式/示例调用 | **`metric`**（默认已含） |
| XS 函数签名 / 返回形状 / 示例调用 / 测试示例 | **`vfunc`**（默认已含；别名 `fn`） |
| 域库 API（公告/财报/K线/股息/分部…） | **`vfunc`**（`notice.*` / `filings.*` / `kline.*` / `bonus.*` / `segments.*` / `iofmt.*` / `anchor.*`） |
| 选股索引字段/枚举 | **`screener`** |
| 策略卡 | `strategy` |
| 平台树全文 ripgrep | 显式 `scripts` + scope（深挖；默认不要） |

默认 domains：`symbol|metric|strategy|skill|screener|vfunc|index|industry`。

一次命中尽量带齐下一步：`id` / `ex` 或 `example_call_xs` / `call_spec`（含 `returns_shape`）/ `related`，避免再 discover。

选股 `screener` 搜名时：后端对增速族做同义扩展；未提「行业」时公司字段优先于 `$CUR_IND_*`。仍无命中 → 换词再搜；仍无 → `wm-screen-index` / 分析师 + `wm-xs-eval-guide`（**禁止**第三方选股）。

### 何时不要用

- 已明确 skill id 且只要 run → 直接 `skills/run`
- 已有代码且只要行情/财务卡 → 直接对应 L1
- **执行选股筛池** → `wm-screen-index` `action=conditions`
- 写短 XS → `wm-xs-eval-guide`（先用本接口对齐 `$` / 函数名）

### 调用

`POST {WINMALE_API_BASE}/v1/analysis/xs/discover`

#### 发现技能（优先）

```json
{
  "q": "历史股息",
  "domains": ["skill"],
  "market": "cn",
  "limit": 10
}
```

#### 指标定义

```json
{
  "q": "ROE",
  "domains": ["metric"],
  "market": "cn",
  "limit": 10
}
```

#### 公司 / 证券代码

```json
{
  "q": "贵州茅台",
  "domains": ["symbol"],
  "market": "cn",
  "limit": 5
}
```

#### 行业 / 指数（别名一次给齐）

```json
{
  "q": "白酒",
  "domains": ["industry"],
  "limit": 5
}
```

```json
{
  "q": "沪深300",
  "domains": ["index"],
  "limit": 5
}
```

#### 函数 / 域库 / 示例（静态索引，默认开放）

```json
{
  "q": "年同比",
  "domains": ["vfunc"],
  "limit": 10
}
```

```json
{
  "q": "公告 减持",
  "domains": ["vfunc"],
  "limit": 10
}
```

```json
{
  "q": "filings.query",
  "domains": ["vfunc"],
  "limit": 5
}
```

#### 其它域

```json
{
  "q": "湖南",
  "domains": ["screener"],
  "scopes": ["name", "code", "content"],
  "market": "cn",
  "limit": 20
}
```

| domain | 说明 |
|--------|------|
| **`skill`** | SkillHub 官方技能 |
| **`symbol`** | 公司 / 证券代码 |
| **`index`** | 指数：`id=index.hs300` + `example_call_xs` + `related` |
| **`industry`** | 行业：`id=industry.S34` + `example_call_xs` + `related` |
| `metric` | `$` 指标；`definition` / `formula` / `example_call_xs` |
| **`vfunc`** | 静态索引：内核/host 函数 + **脚本域库** + tests/smoke 示例（`kind=vfunc|example`） |
| `screener` | 选股索引（需 `user:screener:indicator:read`） |
| `strategy` | 策略卡 |
| `workspace` / `scripts` | 用户文件 / 平台脚本树全文（scripts 需额外 scope） |

### 如何读结果

- `hits[]`：`domain` / `id` / `title` / `snippet` / `matched_fields`
- **`domain=skill`**：`id`=`wm-*` → `POST /v1/skills/{id}/run`
- **`domain=symbol`**：`id`=证券代码 → 公司卡等 L1
- **`domain=index|industry`**：直接用 `id` 写 XS；`related` 可 `skills/run`；不必再 discover
- **`domain=metric`**：`definition` / `formula` / `example_call_xs`
- **`domain=vfunc`**（读齐再写 XS；禁止只看函数名 invent 参数）：
  - `ex` / `example_call_xs`：可直接抄的示例调用（优先用这个）
  - `call_spec`：`min_args` / `max_args` / `args[]` / `want_hint` / `returns` / `returns_label`
  - `call_spec.returns_shape`：**结构化返回契约**（复杂 map/arr 必读）
    - `kind=object` → 读 `fields[]`（`name` / `type` / `cn` / `optional`）
    - `kind=array` → 读 `items`
    - `kind=union` → 读 `variants[]`（如 `backtest.await_event` 命中 vs 超时）
    - `kind=opaque` → 真正动态 JSON，勿假装固定键
    - 标量 `returns=bool|int|string|float64` 时 **可以没有** `returns_shape`
  - `examples[]`：tests/smoke 挂接（`path` + `blurb` + `syntax`），可选
  - 覆盖面：内核 UPPERCASE、host（`screener.*` / `backtest.*` / `watchlist.*`…）、脚本域库（`notice.*` / `filings.*` / `kline.*` / `bonus.*` / `segments.*` / `iofmt.*` / `anchor.*` / `simulation.*`）
- **`domain=screener`**：`id`=field；content 时带 `value`、`suggested_op`
- `partial.*`：某域失败时其它域仍可能有结果

### 之后

1. **`skill` → `skills/{id}/run`（先做这个）**
2. `symbol` → 公司卡等 L1
3. `index` / `industry` → `wm-index-members` / `wm-industry-members` 或直接 XS
4. `screener` → `wm-screen-index` `conditions`
5. `metric` / `vfunc` → 抄 `ex` + 按 `returns_shape` 解析；再 `wm-xs-eval-guide` 或卡片 include
6. 已有专用技能时（如公告 → `wm-notice-radar`）优先 `skills/run`；`vfunc` 域库用于补参数/返回形状或技能盖不住的边角

### 禁止

- 跳过 skill 发现、直接用 `wm-notice-radar` / 裸 eval 代替已有专用技能
- 用本技能代替 `wm-screen-index` 跑筛池
- invent 未命中的 `$` / skill id / 函数名 / `index.*` / `industry.*`
- 忽略 `call_spec` / `returns_shape`，凭印象编参数或解析返回 map
- 为查函数或指标定义去默认扫全平台 scripts（须显式 domain + scope）
- 选股字段搜不到就改走 westock / 同花顺 / 东财等第三方工具
