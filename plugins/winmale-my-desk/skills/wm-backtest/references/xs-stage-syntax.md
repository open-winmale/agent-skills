# 阶段脚本 XS 语法速查（作者面）

完整语言面见 **wm-xs**。这里只列回测阶段里最常踩的写法。

## 必备骨架

```xs
xs.require("xs/simulation/lib/init.xs")   # trading/risk 几乎总要
# selector filter 可用 trace.xs；用到 pe_ttm/bar_ok/append_order 必须 init

# @param take_profit_pct number default=0.10
# ↑ 声明后才能进 script_params / tuning

return ...   # 各阶段返回形状见 stages.md
```

| 阶段 | 返回 |
|------|------|
| selector filter | `bool` |
| selector_rank | `ARR{symbol...}` |
| trading | `ARR{ ARR{sym, side, wt, price, reason}, ... }` |
| risk | 过滤后的同形 proposals（或 nil） |

## 高频语法

| 写法 | 说明 |
|------|------|
| `name := expr` / `name = expr` | 赋值；优先 `:=` |
| `func(a, b) { ... }` | 函数；阶段正文顶层通常直接算 |
| `ARR{1, 2}` / `MAP{"k": v}` | 字面量 |
| `for i := 0; i < LEN(xs); i++ { }` | 循环 |
| `if cond { } else { }` | 分支 |
| `STRING(x)` / `FLOAT(x)` / `DEFAULT(x, 0)` | 转换与空值 |
| `HAS(map, key)` / `KEYS(map)` / `LEN(arr)` | 容器 |
| `simulation.tuning("k", default)` | 读 `# @param` / override |
| `simulation.bar(sym)` / `last_price(sym)` | 现价；缺 bar 时按 `bt.date` PIT 补 |
| `simulation.append_order(out, sym, side, wt, reason)` | 提案；`wt≤0.001` 跳过并 `WEIGHT_SKIP` trace |
| `simulation.rule("take_profit")` | 规则计数 → `metrics.rule_counts` |

### 手数 / 权重（A 股）

买入股数 ≈ `floor(NAV × weight / price / 100) × 100`。  
例：NAV=100 万、价=10、`weight=0.03` → 约 3000 股（可行）；价过高或 weight 过小 → 0 股 → ledger `risk_reject`（summary 里 `metrics.rule_counts.risk_reject` / `risk_reject_zero_qty`）。

### 基准

CN 默认基准 **`index.hs300`**（沪深 300）。L1 可用 `args.benchmark` 覆盖（写入 ConfigOverride）。

## 常见报错对照

| 现象 | 怎么处理 |
|------|----------|
| lint：`unexpected token` / 括号不配 | 先 `wm-xs` check；阶段里少写嵌套三元，拆成临时变量 |
| `unknown script param "x"` | 在对应阶段补 `# @param x ...` 再 sync；override 键名须一致 |
| `pe_ttm`/`bar_ok` 恒空 | 缺 `init.xs`（lint 会拦） |
| 有持仓但 `bar_ok=false` | 引擎补持仓 flat bar；策略用 `simulation.bar` / `last_price`（勿猜 `price`） |
| 下单无成交 / `WEIGHT_SKIP` / `risk_reject` | weight 太小或不足一手；见上式；看 `rule_counts` |
| `UNIT_EXISTS` | 同 `unit_id` 默认覆盖；仅 `overwrite=false` 才硬失败 |
| `ARGS_REQUIRED` | skills/run body 必须 `{"args":{...}}`，勿扁平 `{"action":...}` |

## 改完先夹具

见 [stage-test.md](stage-test.md)。示例：`examples/xs/stage_harness/`。
