# 引擎面：simulation 库与 bt.* / book

加载：`xs.require("xs/simulation/lib/init.xs")`（trace → … → portfolio → quote → quote_ta → fundamental → state）。  
查源码：`backtest.lib_read("xs/simulation/lib/portfolio.xs")`（host）。未 load / 非日环 → `pe_ttm`/`bar_ok` 会空或恒 false。

Probe 时 `bt.live=true`：`simulation.pb` / `pe_ttm` / `mv` / `chg` / `rsi` / `kdj` / `macd` 用 forming last；裸 `$PB_TTM` / `$RSI_14` 仍是昨收。回测 `bt.live=false` 与 SAS 一致。

**硬规则**：写 trading/risk **禁止猜字段**。`bt` / `book` / `positions` / `bar` 字段以下表为准；没有的键（如 `pos.cost`、`pos.price`）不存在。

## 关键结构体：`bt`（引擎日上下文，只读）

| 键 | 类型 | 含义 |
|----|------|------|
| `bt.live` | bool | probe forming/tip；回测日环 false |
| `bt.date` | string `YYYY-MM-DD` | 当前模拟日 |
| `bt.ts` | int unix | 当日 0 点 |
| `bt.day_index` | int | 日序号 |
| `bt.is_week_start` / `is_month_start` | bool | 日历锚 |
| `bt.selector_refreshed` | bool | 今日是否刚跑 selector |
| `bt.candidates` | `string[]` | 选股池（sticky；非刷新日保持上次） |
| `bt.universe` | `string[]` | list 模式扫描宇宙 |
| `bt.bar` | `MAP{sym → bar}` | 当日 K 线视图（见下） |
| `bt.benchmark` | MAP | 基准 close/nav |
| `bt.corporate` | MAP | 当日公司行为 |
| `bt.proposals` | ARR | trading 输出（risk 读）；元素为 `ARR{sym, side, weight, price, reason}` |
| `bt.params` | MAP | `simulation.tuning` 读这里 |
| `bt.config` | MAP | run 级只读元数据 |
| `bt.group_tags` / `group_limits` | MAP | 组合打标/上限 |
| `bt.history` | ARR | 已提交日步骤 |
| `bt.today` | MAP | 当日步骤（含 `today.book` → 与顶层 `book` 同引用） |
| `bt.trace` | ARR | trace 缓冲 |

**禁止** `SET`/`vset` 改写 `bt`。

### `bt.bar[sym]`（当日行情行）

键必须 `STRING(sym)`。

| 字段 | 含义 |
|------|------|
| `open` / `high` / `low` / `close` | OHLC |
| `volume` / `amount` | 量 / 额 |
| `pre_close` / `change` / `percent` | 昨收与涨跌（probe forming；回测日 K 常为 0） |
| `source` | `probe_tip` / `kline` / `held_fill` |

**现价（交易日）**：优先 `simulation.last_price(sym)` 或 `simulation.bar(sym).close`。  
`simulation.bar` / `ensure_bar`：已有有效 `bt.bar` → 直接返回；否则按 **`bt.date` PIT** 拉 `kline.*` 写回（`source=kline`）；再否则持仓用 `last_price`/`avg_cost` 合成（`source=held_fill`）。禁止偷看未来 / 实时。  
`bar_ok` **只读**已有 `bt.bar`（不自动拉库，避免扫候选池时放大）；持仓监控请用 `bar`/`last_price`。  
**禁止**猜 `pos.price` / `pos.cost`。

## 关键结构体：`book`（账本，只读）

| 键 | 类型 | 含义 |
|----|------|------|
| `book.cash` | float | 可用现金 |
| `book.nav` | float | 净值 |
| `book.as_of` | string | 账本日 |
| `book.positions` | `MAP{sym → position}` | 持仓表 |

**禁止**改写 `book`。

### `book.positions[sym]`（持仓行）— 仅下列字段

| 字段 | 含义 | 勿用别名 |
|------|------|----------|
| `quantity` | 持股数 | — |
| `sellable` | 可卖数量（A 股 T+1） | — |
| `avg_cost` | **建仓均价** | ❌ `cost` / `price` |
| `last_price` | 最近标记价（日终/撮合更新） | ❌ `price`；盘中浮盈优先 `bt.bar.close` |

```xs
# ✅ 正确
cost := simulation.position_cost(sym)   # = avg_cost
px := simulation.last_price(sym)       # bar → last_price → avg_cost
qty := simulation.position_qty(sym)
bar := simulation.bar(sym)             # 缺则 PIT 补写 bt.bar

# ❌ 禁止猜测
# pos.cost / pos.price
```

浮盈：`px / cost - 1`（`cost>0 && px>0`）。

## `bt.config` / 调参

常用：`unit_id`、`start`/`end`、`selector_freq`、`execution_timing`、`risk.max_single_position_pct` …  
访问：`simulation.config_str/num/bool("key", default)`（支持 `risk.xxx` 点路径）。  
用户阈值：`simulation.tuning("max_pe", 15)` ← sync 后即声明，可被 `script_params` / UI 覆盖。  
`# @param` **可选**（补 group/ref/advanced）；内部常量用字面量，不要 `tuning`（否则会进 UI）。  
向未声明的 key 塞 override → 拒收。

## 按模块：常用 API

### fundamental.xs / quote.xs

| API | 说明 |
|-----|------|
| `simulation.pe_ttm` / `pb` / `ps_ttm` / `pr` / `mv` | 估值；**probe 用 last×股本**，勿裸 `$PE_TTM` |
| `simulation.roe` / `debt_ratio` / `ncfo` | 无价格腿，PIT 即可 |
| `simulation.chg` / `ma` / `percent` / `bias` | 技术；probe 按 last 缩放 SAS 窗口 |
| `simulation.rsi` / `kdj` / `macd` / `boll` | 盘中重算序列（DEA/RSI/KDJ）；回测读 SAS |
| `simulation.rsi` / `kdj` / `macd` / `boll` | 盘中重算序列（DEA/RSI/KDJ）；回测读 SAS |
| filter 内无价格腿 | 可直接 `$ROE_TTM`；**估值仍建议 `simulation.pb(symbol)`** |

**正确**：`xs.require(init)` 后 `simulation.pb(STRING(sym))`。  
**错误**：trading 里对非游标标的裸写 `$PB_TTM`；probe 里拿 `$PE_TTM` 当盘中估值。

### portfolio.xs

| API | 说明 |
|-----|------|
| `simulation.bar(sym)` / `ensure_bar` | 确保当日 bar（PIT 补写）；见上 |
| `simulation.last_price(sym)` | 当日可用价 |
| `simulation.bar_ok(sym, min_vol)` | 已有 bar 且 `close>0`+量能（不拉库） |
| `held_symbols()` | `KEYS(book.positions)` |
| `position_qty(sym)` | `quantity` |
| `position_cost(sym)` | **`avg_cost`**（无持仓→0） |
| `append_order(...)` | 拼提案（weight≤0.001 → `WEIGHT_SKIP`） |
| `bar_diag(sym)` | 诊断；必要时尝试 `bar` 补价 |

### state.xs / trace.xs

| API | 说明 |
|-----|------|
| `state_get/set` | 跨日 scratch（`bt.state`；勿 SET 改账本） |
| `rule(code)` | 规则触发计数 → `bt.rule_counts`；跑完进 `summary.metrics.rule_counts` |
| `append_order` | `wt≤0.001` 跳过并 `WEIGHT_SKIP` trace（非静默） |
| `trace` / `tuning` / `factor` | 可观测与参数 |

指标对照与 PIT 边界：[metric-availability.md](metric-availability.md)。  
阶段夹具单测：[stage-test.md](stage-test.md)。

### config / group / status / events / corporate

- `config_*` → `bt.config`（含 `risk.max_position_pct_by_symbol`）  
- `group_tag` → 组合权重  
- status / corporate / events → ST、除权、事件  

## 查库与写脚本

1. 仿真库：`backtest.lib_read("xs/simulation/lib/<file>.xs")`  
2. 拨测夹具：`xs.require("xs/simulation/test/harness.xs")` → `test_fixture`  
3. 官方单元：`xs/backtest/equal_weight_buy_hold/`；示例 `examples/xs/*`  
4. **函数名** → wm-discover / wm-xs；**字段** → 本页；禁止 invent  
5. 取数：**先包裹后兜底**（防未来函数）  
6. 起草校验 → **wm-xs** → `lint` / `preview_custom` / `run_custom`  
