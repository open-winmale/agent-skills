# 选股指标用法 Playbook（Agent）

字段对齐：**先 `action=indicators`（+ 轻量 alias）**；需要描述/内容穿透时再 **`wm-discover` `domains=["screener"]`**（或本技能 `action=search`，同源）。

自然语言 → `_MIN` / `_AVG` / `_TREND` 等范式见 [semantic-patterns.md](semantic-patterns.md)。  
详见 SKILL「字段对齐决策树」。返回形态见 `docs/design/SKILL_RETURNS_CONTRACT.md`。

---

## 0. 原始值单位

| 类型 | 存储 | conditions |
|------|------|------------|
| 比率 / 股息率 / ROE / 负债率 | 小数（`0.04`=4%） | `"0.04"` 或 `"4%"` |
| PE / PB / 倍数 | 真实倍数 | `"30"` |
| 金额 | 元；选股 NCFO 总量多为「亿」口径看字段说明 | 可用 `100Y` 等字面量 |
| 枚举 / MULTI | 字符串码 | discover/`indicator_distinct` 后再 `EQ`/`IN`/`HAS` |

`action=indicators` / `search` 返回已是 **Agent 投影**：

- 用 `value_scale` + `default_value` / `example_condition_value` 写阈值
- `display_unit` / `display_default_val` 仅 UI 刻度（如 `%` + `15`），**禁止**原样进 `scalar.value`
- 例：ROE → `value_scale=ratio`，`default_value="0.15"`（不是 `"15"`）

禁止对比率反复 ÷100。见管家 `units-and-values.md`。

---

## 0b. indicators 轻量 alias（口语 → keyword）

`action=indicators` 会对以下关键词做精确替换后再按名过滤（`keyword`/`q` 互通）：

| 口语 / 试错词 | 解析为 |
|---------------|--------|
| 现金流画像 / 八型 / CF_KIND | 现金流特征 |
| PE分位 / 估值分位 / 低估 | PE分位 |
| 股息 | 股息率 |
| 市盈率 / 市净率 / ROE | 同名 |

**不够用时**：换词再 `indicators`；仍要内容匹配 → discover screener（如 `q=PCB`）。

---

## 1. 窗口：连续/近 N 年 → MIN / AVG / TREND

索引无「连续 N 年次数」COUNT。常用：`{METRIC}_{3|5|10}Y_{MIN|AVG|TREND}_LAST`。  
例：连续五年分红 ≈ `$BONUS_5Y_MIN_LAST > 0`（代理，须披露）。

---

## 1b. 搜字段：同义族 + 内容穿透

| 场景 | 走 |
|------|-----|
| 已知大概中文名 | `indicators` keyword |
| 描述/内容里含词（PCB、概念、枚举文案） | `wm-discover` `domains=["screener"]`（或 `action=search`） |
| 已知 field 要全枚举 | `indicator_distinct` |

后端会对**增速族**做同义扩展。Agent 侧：

| 口语意图 | 可互换代理（须披露） |
|----------|----------------------|
| 整体利润/扣非增速找不到或不够用 | 同口径 **每股** 增速（EPS/每股扣非等） |
| 「几何增速」与「增速 / 同比 / 增长率」 | 选股筛池可互作近似；优先同窗口（3/5/10 年）同主体 |
| 只要公司字段 | 勿默认挑 `$CUR_IND_*`；查询未提「行业」时优先非行业字段 |

搜不到时：**换词再一轮**，仍无 → §8。禁止为单个口语写死条件配方。

---

## 2. 分红率 ≠ 股息率

| 口语 | field 族 |
|------|----------|
| 分红率 / payout | `$BONUS_TTM_RATE_*` |
| 静态股息率 | `$BONUS_RATE_LYR_*` / `$BONUS_RATE_*Y_*` |
| 每股分红 | `$DPS_*`（元） |

---

## 3. 枚举 / 标签 / 地区 / 产品 / 现金流画像

```text
indicators →（内容穿透）discover domains=["screener"] q=…
→ id=field, value, suggested_op → conditions
```

已知 field 要全表：`indicator_distinct`。禁止臆造中文枚举。

### 现金流特征码（对齐 `sys/metric/screen_cf.xs`）

筛池字段：`$CF_KIND_CODE_{3,5,10}Y_LAST`（公司）/ `$CUR_IND_CF_KIND_CODE_*`（行业）。  
**不是**分析指标 `$CF_KIND`（分析用，勿当筛池 field）。

单年符号 → 数字（查询用数字串；多年如 `222`）：

| 符号 | 数字 | 名 |
|------|------|-----|
| `+-+` | `0` | 蛮牛 |
| `++-` | `1` | 老母鸡 |
| `+--` | `2` | **奶牛** |
| `+++` | `3` | 女巫 |
| `---` | `4` | 蝙蝠 |
| `--+` | `5` | 赌徒 |
| `-+-` | `6` | 躺平 |
| `-++` | `7` | 咸鱼 |

「稳健」代理常用奶牛 `2` / 老母鸡 `1`（须披露为代理）。**勿**写反成「1=奶牛」。

---

## 4. fieldCompare 与 NCFO 口径

| 需求 | field | 勿用 |
|------|-------|------|
| 经营现金流**总量** | `$NCFO_TTM_LAST`（看单位说明，多为亿） | `$PS_NCFO_*` |
| 每股经营现金流 | `$PS_NCFO_TTM_LAST`（元/股） | 当成总量 |
| 每股现金覆盖股息 | fieldCompare `$PS_NCFO_*` vs `$DPS_*` | — |

`indicators`/`discover` 若带 `compare_targets`：

```json
{
  "type": "INDICATOR",
  "field": "$PS_NCFO_TTM_LAST",
  "operator": "GTE",
  "value": {
    "fieldCompare": { "field": "$DPS_TTM_LAST", "label": "覆盖每股股息", "coefficient": 1 }
  }
}
```

---

## 4b. 条件算子 cookbook（EQ / IN / HAS / BETWEEN）

集合类读 **`value.set.values`**（也兼容误写的 `value.list`）。**不要**只写 `value: ["a","b"]`。

| 算子 | 适用 | value 形状 |
|------|------|------------|
| `EQ` / `GTE` / `LTE`… | 标量 | `{"scalar":{"value":"…"}}` |
| `IN` / `HAS` / `NOT_HAS` | 枚举/标签多选 | `{"set":{"values":["a","b"]}}` |
| `BETWEEN` | 数值窗口 | `{"range":{"min":"10","max":"25"}}` |

**EQ（比率用小数）**

```json
{
  "type": "INDICATOR",
  "field": "$ROE_TTM_LAST",
  "operator": "GTE",
  "value": { "scalar": { "value": "0.15" } }
}
```

**IN（国资：央企或地方国企）**

```json
{
  "type": "INDICATOR",
  "field": "$ORG_TYPE_TAG",
  "operator": "IN",
  "value": { "set": { "values": ["央企", "地方国企"] } }
}
```

**HAS（行业中文名 / 标签）**

```json
{
  "type": "INDICATOR",
  "field": "$INDUSTRY_TAGS",
  "operator": "HAS",
  "value": { "set": { "values": ["公用事业"] } }
}
```

**BETWEEN**

```json
{
  "type": "INDICATOR",
  "field": "$PE_TTM_LAST",
  "operator": "BETWEEN",
  "value": { "range": { "min": "10", "max": "25" } }
}
```

| 错写 | 正确 |
|------|------|
| `"value":{"list":["央企","地方国企"]}` | `"value":{"set":{"values":[…]}}`（list 现已兼容，仍推荐 set） |
| `"value":["央企"]` | 必须包在 set/scalar/range |
| `$INDUSTRY_CUR_1 EQ "公用事业"` | 该字段是**代码**；中文名用 `$INDUSTRY_TAGS`+`HAS` |

### 行业：码 vs 名

| 目的 | 字段 | 算子 | value 示例 |
|------|------|------|------------|
| 一级行业**代码**精确 | `$INDUSTRY_CUR` / `$INDUSTRY_CUR_1` | `EQ` | `"industry.S64"` |
| 行业**中文名**/标签 | `$INDUSTRY_TAGS` | `HAS` / `IN` | `"公用事业"` |
| 查码 | `wm-industry-members` / discover | — | — |

---

## 5. conditions 返回形状

```text
HTTP: data.result.rows / data.result.row_ids / data.result.where
剥信封 body: rows / row_ids / where / page_hit_count / response_guide
run_id: ""（ad-hoc）→ 禁止伪造 stock_picking.run
```

不要假设顶层 `symbols[]`。不要再读 `result.result.rows`（已拍平）。总数用 `preview_count`。

---

## 5b. 残差下推（慢，不是「不支持」）

条件里的字段若**尚未建进选股索引列**，仍可进 `conditions`，查询走 **residual 残差下推**，比已建列 pushdown **更慢**。

Agent 应：优先已建列；必须用未建列时**披露慢路径**；大宇宙上叠多重残差时先收窄池。

---

## 6. 加列 / 分页（`top_n` 上限 200）

单次最多 **200** 行（manifest `maximum: 200`）。要更多用 `offset`：

```text
第 1 页：top_n=200, offset=0
第 2 页：top_n=200, offset=200
… 直到返回条数 < top_n
```

| 需求 | 做法 |
|------|------|
| 多列 | `fields: ["$SYMBOL","$NAME",…]` |
| 翻页 | 同 conditions + `offset`（步长=top_n） |
| 总数 | `preview_count` |
| 已存策略翻页 | `run_strategy` → 读 `fetch` |

---

## 7. 排序

索引查询**无** ORDER BY。对 `rows` 按列排，或贴 deeplink 让用户点列头。满页说明「本页内排序」。

---

## 8. 索引缺口：缩小池后平台内补算（禁止第三方选股）

产品选股盖不住的口径（逐年序列/自定义公式等）：

```text
1) 能映射的条件先 conditions / preview_count 缩小池（记下 row_ids / where）
2) 缺口直说（缺哪条口径、已筛出多少、是否残差慢路径）
3) 交 role-financial-analyst → wm-xs（INDEX_*；在已缩小集合上算）
```

**禁止**改走 westock / 同花顺 / 东财 / 其它第三方选股或指标 API 补缺口。  
**禁止**全市场裸 CONFT 冒充本产品选股。  
**禁止** shell/glob 翻本地 scripts 仓「自己找索引」。
