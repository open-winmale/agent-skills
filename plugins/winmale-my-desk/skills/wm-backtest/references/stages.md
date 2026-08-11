# 引擎面：阶段契约

源：`winmale/biz/backtest/docs/SCRIPT_CONTEXT.md`、`BACKTEST_TDD.md`。  
官方单元：`xs/backtest/<unit_id>/`。共享库：`xs/simulation/lib/`（**不是**阶段目录）。  
写复杂 XS → **wm-xs**，再经管理面 lint / run_custom 挂上。  
**每改完一个阶段**：先用 [stage-test.md](stage-test.md) 夹具 `CHECK`，再 lint。

## 日环顺序

```text
selector (filter 并发 per-symbol | list 一次)
  → selector_rank（对 bt.candidates；返回 symbol[]）
  → trading（[]OrderProposal）
  → [可选 group_label]
  → risk（软裁剪）→ Go 硬限额 → match
```

| 调度概念 | 谁管 | 说明 |
|----------|------|------|
| `selector_freq` | 引擎配置 | 多久刷新候选人；**≠调仓** |
| `bt.selector_refreshed` | 日状态 | 今日是否刚跑 selector |
| `bt.candidates` | 引擎 sticky | 非刷新日保持上次池 |
| 再平衡 | **trading.xs** | 如 `simulation.should_rebalance("monthly")` |
| `execution_timing` | 引擎配置 | 何时成交；脚本只读 |

## selector

| `script_role` | `project_write` stage | 返回 | 上下文 |
|---------------|----------------------|------|--------|
| **filter**（默认种子） | `"selector"` | **bool** 每票 | 当前 `symbol` 已设游标；可用 `$METRIC` |
| **list** | `"selector"` | **symbol 数组** | `bt.universe` 已注入 |

种子 `equal_weight_buy_hold` = filter：

```xs
xs.require("xs/simulation/lib/trace.xs")
return !$IS_ST
```

自定义 filter：

```xs
return !$IS_ST && $PE_TTM > 0 && $PE_TTM < 15
```

**模式契约**：filter selector 必须返回 bool；list selector 必须返回 symbol 数组。并发 filter 勿用外层累计变量重赋值。
回测禁用 `_LAST` / 实盘 INDEX 捷径。

## selector_rank

输入 `bt.candidates`；必须返回 **symbol 列表**（可 SORTBY/TOPK 后截断）：

```xs
pool := bt.candidates
if LEN(pool) == 0 { return nil }
return pool
```

错误：`return $ROE_TTM` → 标量。  
**list + rank**：lint 警告，运行时 **忽略 rank**。

## trading

返回 `[]OrderProposal` 或 nil：

```text
[sym, "BUY"|"SELL", weight, price?, reason?, priority?]
```

| 字段 | 含义 |
|------|------|
| weight BUY | 占**可用现金**比例（0~1） |
| weight SELL | 占**可卖持仓**比例 |
| price | 0=用收盘参考；**非限价单** |
| priority | 越小越先处理（可选） |

```xs
xs.require("xs/simulation/lib/init.xs")
w := invest_pct / FLOAT(n)   # 比例，不是 pay=cash/n
out = simulation.append_order(out, sym, "BUY", w, "ew")
return out
```

读取跨标的估值/质量指标时，优先 `SETCURSORXS(sym)` 后读取 `$METRIC`，或使用 `simulation.pe_ttm(sym)`；不要依赖未切游标的裸 `$PE_TTM`。

上下文：`book` / `bt` 字段见 [simulation-api.md](simulation-api.md)（**白名单**；勿猜 `pos.cost`/`pos.price`）。  
常用：`book.nav`/`cash`/`positions[sym].avg_cost|quantity|sellable|last_price`，`bt.candidates`/`universe`/`bar[sym].close`/`date`/`params`。  
持仓成本优先 `simulation.position_cost(sym)`；现价优先 `bt.bar[STRING(sym)].close`。

## risk

输入 `bt.proposals`；返回过滤后的提案或 `{orders:…}`。推荐保留 Go `fallback_go_rules` 做硬限额。可用 `bar_ok`、跨标的指标库。

## group_label（可选）

组合打标 → `bt.group_tags`；Composer/blocks。L1 `run_custom` 默认不写该 stage。

## Workspace

内容 SoT：`project_write` → `project_publish`。勿对 workspace 绑定 unit 用 `template_*` 改脚本。

## script_params

`script_params` 不是任意键值覆盖。只有参数已在 case `params` 声明、阶段脚本含 `# @param` 元数据，或项目同步后由 `simulation.tuning(...)` / `backtest.tuning(...)` 提取为声明参数时才会接受；未声明的 role/key 会在校验时拒绝。
