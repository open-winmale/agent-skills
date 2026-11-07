# 阶段脚本拨测夹具（必读 · Agent 硬流程）

写完 / 改完任一阶段脚本（`selector` / `selector_rank` / `trading` / `risk`）后，**先用本夹具单测，再 lint / preview / run_custom**。  
不要一上来跑完整 Engine WarmUp。

库路径（平台 scripts 仓，正式/拨测 EC 均可 `xs.require`）：

```text
xs/simulation/test/harness.xs
```

Skill 包内可跑示例：`examples/xs/stage_harness/`（本目录）。

## Agent 硬流程（每一步）

```text
写/改 stage.xs
  → require harness + test_fixture（或内置 held_out_of_pool）
  → xs.call / 粘贴阶段正文（或只测其中一段逻辑）
  → CHECK 断言（返回形状、止盈是否触发、bar_ok、position_cost…）
  → 通过后再 lint → preview_custom → run_custom
```

| 阶段 | 夹具要准备什么 | 断言什么 |
|------|----------------|----------|
| selector filter | 一般不需要 bt.bar；用 wm-xs/`xs/check` 即可 | 返回 bool |
| selector_rank | `candidates` | 返回 symbol[]，长度/排序 |
| trading | `cash/nav/bars/positions/candidates/params` | proposals 元组；止盈/买入 reason |
| risk | `proposals` + `bars` + book | 过滤后列表；ST/量能裁剪 |

**禁止**：猜 `pos.price`/`pos.cost`；未夹具就声称「逻辑已验证」。

## 最小示例

```xs
xs.require("xs/simulation/test/harness.xs")

simulation.test_fixture(MAP{
  "date": "2024-06-03",
  "cash": 200000,
  "nav": 1000000,
  "candidates": ARR{"000858"},
  "bars": MAP{
    "600519": MAP{"close": 1800, "volume": 1e6},
    "000858": MAP{"close": 150, "volume": 1e6},
  },
  "positions": MAP{
    "600519": MAP{"quantity": 100, "avg_cost": 1500, "last_price": 1800},
  },
  "params": MAP{"take_profit_pct": 0.10},
})

# 持仓不在 candidates，仍应能取现价/成本
CHECK(simulation.bar_ok("600519", 0), "held bar")
CHECK(simulation.position_cost("600519") == 1500, "avg_cost")
pnl := bt.bar["600519"].close / simulation.position_cost("600519") - 1
CHECK(pnl > 0.1, "take-profit condition")
return MAP{"ok": true, "pnl": pnl}
```

内置一键：`simulation.test_fixture_held_out_of_pool()`。  
包内示例：
- `@pack:wm-backtest/examples/xs/stage_harness/smoke.xs`
- `trading_take_profit_check.xs`
- `selector_rank_check.xs`
- `risk_drop_nobar_check.xs`

仓库冒烟：`xs/tests/simulation/stage_harness_smoke.xs`。

## API 一览

加载：`xs.require("xs/simulation/test/harness.xs")`（内部已 `require init`）。

| API | 参数 | 作用 |
|-----|------|------|
| `test_reset()` | — | 清空/重置 bt、book 可测空壳 |
| `test_clock(date)` | `YYYY-MM-DD` | `bt.date` / `book.as_of` |
| `test_book(cash, nav, positions)` | float, float, MAP | 现金净值持仓表 |
| `test_position(sym, qty, avg_cost, last_price)` | — | 单票持仓行（字段白名单） |
| `test_bar(sym, close, volume)` | — | 单票 OHLC（open=high=low=close） |
| `test_candidates(syms)` | ARR | sticky 候选池 |
| `test_universe(syms)` | ARR | 扫描宇宙 |
| `test_params(params)` | MAP | → `bt.params`（`tuning`） |
| `test_proposals(props)` | ARR | risk 输入提案元组 |
| `test_fixture(opts)` | MAP | 一键组装（见下） |
| `test_fixture_held_out_of_pool()` | — | 持仓∉candidates 但仍有 bar |

### `test_fixture(opts)` 键

| 键 | 类型 | 说明 |
|----|------|------|
| `date` | string | 默认 `2024-03-04` |
| `cash` / `nav` | float | 默认 50万 / 100万 |
| `candidates` / `universe` | ARR | 可选 |
| `params` | MAP | tuning |
| `proposals` | ARR | risk |
| `bars` | `MAP{sym: close}` 或 `MAP{sym: MAP{close,volume}}` | 行情 |
| `positions` | `MAP{sym: qty}` 或 `MAP{sym: MAP{quantity,avg_cost,last_price}}` | 持仓 |
| `config` | MAP | 可选写入 `bt.config` |

返回摘要 MAP：`date/cash/nav/candidates_n/positions_n/bars_n`。

源码权威：`backtest.lib_read("xs/simulation/test/harness.xs")`。

## Go 夹具（引擎单测）

```go
bec, err := NewStageEvalContext(HeldOutOfPoolFixture())
raw, err := bec.EvalCaseScript(CaseScript{Name: ScriptNameTrading, Body: body})
```

见 winmale `biz/backtest/stage_fixture.go`。

## 边界

- 夹具写 `bt`/`book` 仅拨测（`@export_policy state.write.runtime`），不是策略里改账本。
- 正式 run 仍由引擎 `BindBookSnapshot`；取数仍 **simulation.*/bt.* 包裹优先**（防未来函数）。
- OpenAPI：`{"args":{...}}`；顶层裸 `action` → 400。
