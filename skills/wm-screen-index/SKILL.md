---
name: wm-screen-index
display_name: "条件选股"
version: 1.9.0
description: 按选股索引条件批量筛股票池；也可列出/跑/保存我的策略。不是单只公司查询。
---

# 条件选股

选股产品（StockPicker）的执行入口。

`conditions` / `preview_count` / `run_strategy` 返回 `freshness.index_quote_date`（分市场：`cn`/`hk`/`us`）：选股索引行情截面日，由 query_index EOD 写入 `qi_index_quote:{market}`（长 TTL，同 key 覆盖续期）。

## 对人

批量按条件筛池、跑/存我的策略；不是查单只股票画像。

## 对 Agent

### 字段对齐路由（硬规则）

```text
1) 优先 action=indicators（+ 轻量口语 alias；keyword/q 互通）
2) 需要描述/内容穿透（如「PCB」出现在字段说明里）→ wm-discover domains=["screener"]
   （或本技能 action=search，与 discover screener 同源）
3) 拼 action=conditions
   - 索引已建列 → pushdown（快）
   - 索引未建列仍可进 conditions，但走残差下推（慢）；优先改用已建列或先收窄宇宙
4) 产品选股仍盖不住的口径 → 缩小池后交 role-financial-analyst + wm-xs-eval-guide
```

| 任务 | 做法 |
|------|------|
| 按名找选股字段（PE/ROE/现金流特征…） | **`action=indicators`**（先于 discover） |
| 描述/内容/取值穿透（PCB、地区名等） | **`wm-discover` `domains=["screener"]`** → `id`+`value`+`suggested_op` |
| 已知 field、要完整枚举表 | `action=indicator_distinct` |
| 执行筛池 | **`action=conditions`**（可 `fields`/`offset`） |
| 命中约数 | `action=preview_count` |
| 我的策略 | `list` / `run_strategy` / `save_strategy` |
| 自定义序列/公式缺口 | **先**能筛的 conditions 缩小池 → 缺口直说 → **`role-financial-analyst` + `wm-xs-eval-guide`** |

**禁止** `action=nl`。  
**禁止**缺口时改走 westock / 同花顺 / 东财等第三方选股。  
**禁止**跳过 indicators、只用 metric invent 字段冒充可筛。  
**禁止**把「残差下推（慢）」说成「不支持」。  
**禁止** shell/glob 翻本地仓找字段。

单位、窗口命名、增速同义/代理、fieldCompare、缺口交接 → [references/playbook.md](references/playbook.md)。  
Host 速查 → [references/lib.md](references/lib.md)。  
**eval 直调菜谱** → [references/recipes.md](references/recipes.md)；坑 → [references/pitfalls.md](references/pitfalls.md)。  
返回形态合同 → SkillHub `docs/design/SKILL_RETURNS_CONTRACT.md`。

### 超出本技能

```text
1) 本技能 actions 做完能做的（含 indicators alias 与 discover screener 内容穿透）
2) 缺口写清（已筛池子、缺字段、是否走了残差慢路径）
3) 交 role-financial-analyst（wm-xs-eval-guide / INDEX_*，在缩小集合上算）
4) 禁止第三方选股补洞；禁止全市场裸 CONFT 冒充选股
```

### Action 表

| action | 用途 |
|--------|------|
| `indicators` | 按名列字段目录（+ 轻量 alias） |
| `search` | 选股字段/取值搜索（同 discover screener） |
| `indicator_distinct` | 已知 field 拉枚举 |
| `conditions` | 现拼条件筛一页 |
| `preview_count` | 命中约数 |
| `market_meta` / `indexes` | 行业树 / 索引列表 |
| `list` / `run_strategy` / `save_strategy` | 我的策略 |
| `template` | 旧 pe_roe 兼容（勿默认） |

### 快路径（≤3 次 skills/run + 可选 1 次 discover）

```text
1) indicators（已知名/白名单可跳过）
2) 需要内容穿透 → discover screener（或 search）
3) conditions（能映射的一次拼齐；要列传 fields）
可选 preview_count / offset；用户确认后 save_strategy
```

### 调用

`POST {WINMALE_API_BASE}/v1/skills/wm-screen-index/run`  
无顶层 `symbol`；参数全进 `args`。

#### `action=conditions`

```json
{
  "args": {
    "action": "conditions",
    "market": "cn",
    "top_n": 50,
    "fields": ["$SYMBOL", "$NAME", "$PE_TTM_LAST"],
    "conditions": [
      {
        "type": "INDICATOR",
        "field": "$REGIONBK",
        "label": "地区板块",
        "operator": "EQ",
        "value": { "scalar": { "value": "湖南省" } }
      }
    ]
  }
}
```

比率用小数（`0.04`）或带 `%` 字面量。成功后**原样贴** `deeplinks`，并提示可保存。

#### `action=search`

```json
{ "args": { "action": "search", "q": "PCB", "market": "cn", "limit": 20 } }
```

读 `content_hits` / `name_hits`（同 discover screener）。

#### `action=indicators` / `indicator_distinct` / `preview_count`

见 playbook；`indicators` 按名过滤 + 轻量 alias；**不含**描述内容搜（内容用 discover）。

### 读结果

1. `error`：`SCOPE_DENIED` / `VALIDATION_FAILED` / …  
2. 名单在 **`rows`** 或 **`row_ids`**（HTTP：`data.result.rows`）；看 `page_hit_count` / `response_guide`  
3. ad-hoc `run_id` 恒为 `""` → 禁止伪造运行页  
4. 排序：索引无 ORDER BY；对 `rows` 客户端排，或贴 deeplink  

### 禁止

- 用公司卡循环 / 裸 XS 冒充选股产品  
- 把分红率当股息率（或反过来）  
- 把 `$PS_NCFO_*`（每股）当成总量 `$NCFO_*`  
- 对比率猜「÷100」空转  
- 成功后不贴 deeplink  
