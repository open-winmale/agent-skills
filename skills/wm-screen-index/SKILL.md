---
name: wm-screen-index
display_name: "条件选股"
version: 2.0.5
description: 按条件筛一批股票（市盈率、ROE、股息、行业等）；也可列出/跑/保存我的策略。不是单只公司查询。字段对齐优先 indicators，内容穿透再用 search/discover；勿默认 discover 全库。今天/当日涨跌用 $PERCENT_LAST，勿用 $CHG_1D_LAST（EOD 截面）。
---

# 条件选股

选股产品（StockPicker）的执行入口：批量筛池、预估命中、管理我的策略。

## 何时使用

- 「按条件筛一批股票 / 选股 / 筛选低估值高 ROE 股票池」
- 「哪些股票符合 PE<20 且 ROE>15%」
- 「列出 / 执行 / 保存我的选股策略」

## 何时不要用 (When NOT to use)

- **单只公司的基本面/行情/估值查询** → 使用 `wm-company-card` / `wm-valuation`（单票摸底卡）
- **仅看自选关注列表里的股票** → 使用 `wm-watchlist`（关注列表）
- **指数/行业成分名单列表** → 使用 `wm-index-members` / `wm-industry-members`

`conditions` / `preview_count` / `run_strategy` 返回 `freshness.index_quote_date`（分市场 `cn`/`hk`/`us`）：选股索引行情截面日；另有 `live_quote_updated_at` 表示实时行情暖更时刻。

### 涨跌幅字段（必看 · fb_18c6b1c5f0fc8677）

| 口语 | 正确 field | 勿用 |
|------|------------|------|
| 今天 / 当日 / 盘中涨跌、今日涨幅 > X% | `$PERCENT_LAST`（当日涨跌幅·实时） | `$CHG_1D_LAST` |
| 日K 1 日动量、EOD 技术截面 | `$CHG_1D_LAST`（日K1日涨跌·EOD） | 当作「今天」 |

比率同其它字段：`0.01` 或 `1%` = 涨 1%。拼「今天涨」条件前若曾对齐到「近1d」，改成 `$PERCENT_LAST`。

## 怎么跑（一条命令）

```bash
WM="bash .cursor/skills/wm-skillhub/scripts/wm.sh"
# 仓库内可复制样例（含 market + ROE 0.15）：
$WM run wm-screen-index \
  @.cursor/skills/wm-screen-index/examples/request.json --result
```

无顶层 `symbol`；参数全进 `args`：`{"args":{"action":"conditions",...}}`。扁平 body → 易静默错路径 / `ARGS_REQUIRED`。Agent **不要**手搓 oauth / curl。

`top_n` **上限 200**；翻页用 `offset`（见 playbook §6）。`IN`/`HAS` 用 `value.set.values`（见 playbook §4b cookbook）。行业中文名走 `$INDUSTRY_TAGS`+`HAS`，不要对 `$INDUSTRY_CUR_*` 填中文。

### 单位错例（必看）

| 口语 | 正确 scalar | 错误 |
|------|-------------|------|
| ROE ≥ 15% | `"0.15"` 或 `"15%"` | `"15"`（会被当成 1500%） |
| 股息率 ≥ 3% | `"0.03"` 或 `"3%"` | `"3"` |
| PE ≤ 20 | `"20"` | 不要加 `%` |

`action=indicators` 返回的是 Agent 投影：抄 `default_value` / `example_condition_value`，**不要**抄 `display_default_val`（UI 的 `15`）。

### return_shape

成功：`data.result.rows` / `row_ids` / `deeplinks` / `freshness`（`--result` 时直接是 result 对象）。  
失败：看 `error` → 改 field/单位 → **同一** `wm.sh run` 再跑（勿换鉴权姿势）。

---

## 1. 字段对齐决策树（拼 conditions 前 · 目标 ≤1 次对齐查询）

```text
               [用户选股条件]
                       │
       ┌───────────────┴───────────────┐
 [具体指标名]                    [模糊行业/概念/内容]
 (PE、ROE、股息率…)              (PCB、湖南本地股…)
       │                               │
       ▼                               ▼
 action=indicators                 action=search
 （或本地 Grep references/fields/）  （或 wm-discover domains=["screener"]）
       │                               │
       └───────────────┬───────────────┘
                       ▼
                 [对齐后的 field]
                       ▼
              action=conditions
```

- 索引**已建列** → pushdown（快）  
- 索引未建列仍可进 `conditions`，走**残差下推（慢）**——须披露；优先改已建列或先收窄宇宙  
- **禁止**跳过 indicators、metric invent 字段；**禁止** shell/glob 翻平台 scripts 仓找字段  

口语 → 字段的 `_MIN` / `_AVG` / `_TREND` 等范式 → [references/semantic-patterns.md](references/semantic-patterns.md)。  
单位、alias、缺口交接 → [references/playbook.md](references/playbook.md)。  
字段分片 → [references/fields/_index.md](references/fields/_index.md)。

---

## 2. Action 速查

| Action | 用途 | 要点 |
|--------|------|------|
| **`indicators`** | 按名/别名找字段 | **优先**；`keyword`/`q` 互通 |
| **`search`** | 描述/概念/内容穿透 | 同 discover screener；如 `PCB` |
| **`indicator_distinct`** | 已知 field 枚举白名单 | 地区/板块等 |
| **`conditions`** | **执行筛池** | `market`+`conditions`；比率用 `0.05` 或 `5%` |
| **`preview_count`** | 只估命中数 | 条件过宽/过窄预判 |
| **`list` / `run_strategy` / `save_strategy`** | 我的策略 | 按需 |
| `market_meta` / `indexes` | 行业树 / 索引列表 | 少用 |
| `template` | 旧 pe_roe 兼容 | **勿默认** |

**禁止** `action=nl`。

---

## 3. 调用

见上方「怎么跑」。完整条件树也可内联：

```bash
bash .cursor/skills/wm-skillhub/scripts/wm.sh run wm-screen-index '<args_json>' --result
```

### 典型例子（先抄结构，再改阈值）

**A. 高 ROE + PE 不太贵** — 与 [examples/request.json](examples/request.json) 同构：

```json
{"action": "conditions", "market": "cn", "top_n": 50, "fields": ["$SYMBOL", "$NAME", "$ROE_TTM_LAST", "$PE_TTM_LAST"], "conditions": [{"type": "INDICATOR", "field": "$ROE_TTM_LAST", "label": "ROE(TTM)", "operator": "GTE", "value": {"scalar": {"value": "0.15"}}}, {"type": "INDICATOR", "field": "$PE_TTM_LAST", "label": "市盈率TTM", "operator": "LTE", "value": {"scalar": {"value": "20"}}}]}
```

等价：`"15%"`；**不要** `"15"` 当比率。连续多年 ROE 底线 → `$ROE_5Y_MIN_LAST` 等，见 semantic-patterns。

**B. 股息率（≠ 分红率）**

```json
{"field": "$BONUS_RATE_TTM_LAST", "operator": "GTE", "value": {"scalar": {"value": "0.03"}}}
```

### 快路径（≤3 次 wm-skill-run + 可选 1 次内容穿透）

```text
1) indicators（已知名/白名单可跳过）
2) 需要内容穿透 → search 或 wm-discover screener
3) conditions（能映射的一次拼齐；要列传 fields）
可选 preview_count / offset；用户确认后 save_strategy
```

### 读结果

1. `error`：`SCOPE_DENIED` / `VALIDATION_FAILED` / …（`VALIDATION_FAILED` 先查 field/value，勿原样甩给用户）  
2. 名单在 **`rows`** / **`row_ids`**（HTTP：`data.result.rows` 双读）；看 `page_hit_count` / `response_guide`  
3. ad-hoc `run_id` 恒为 `""` → **禁止伪造**运行页 deeplink  
4. 成功后**原样贴** `deeplinks`（`stock_picking.results` 须带 `where`/`strategy_id`，裸结果页会空白），并提示可 `save_strategy`  
5. 排序：索引无 ORDER BY；对 `rows` 客户端排，或贴工作台 deeplink  

---

## 4. 超出本技能（交接）

**先分清**：口语句里很多「连续 N 年…不低于」可用索引 **`_MIN` / `_AVG` / `_TREND`** 代理（见 [semantic-patterns.md](references/semantic-patterns.md)）——**仍走本技能 `conditions`**，须披露代理口径。  
例：连续 3/5 年 ROE>15% → `$CUR_IND_ROE_3Y_MIN_LAST`（或对应扣非/窗口字段）≥ `0.15`，**不要**为此直接甩给 XS。

真正盖不住时再交接：

```text
[索引表达不了的口径：自定义序列公式、非索引宇宙、无对应 MIN/AVG/TREND 代理…]
  → ① 能筛的静态/代理条件先 conditions 尽量缩池（目标 <200）
  → ② 如实写清缺口（缺字段 / 残差慢路径 / 代理不等价处）
  → ③ 交 role-financial-analyst + wm-xs（缩小集合上 XS）
  → 禁止第三方选股；禁止全市场裸 CONFT 冒充产品选股
```

---

## 5. 硬约束

1. 成功后必须贴返回的 `deeplinks`  
2. 禁止同花顺 / 东财 / westock 等第三方选股补洞  
3. **股息率** ≠ **分红率**（`$BONUS_RATE_*` vs `$BONUS_TTM_RATE_*`）  
4. **每股现金流** `$PS_NCFO_*` ≠ 总量 `$NCFO_*`  
5. 比率用小数或带 `%`；禁止自行猜「÷100」空转；金额用 `1e8` / `1Y` 等字面量  
6. 时间窗必须对齐（要 10 年连续分红勿用 `3Y` 字段）  
7. **今天/当日涨跌** → `$PERCENT_LAST`；**禁止**把 `$CHG_1D_LAST`（近1d/EOD）当今天  
8. 禁止公司卡循环 / 裸 XS 冒充选股产品  

菜谱 / 坑： [recipes.md](references/recipes.md) · [pitfalls.md](references/pitfalls.md) · [lib.md](references/lib.md)
