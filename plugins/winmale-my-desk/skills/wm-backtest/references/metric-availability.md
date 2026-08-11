# 指标可用性对照表（防未来函数）

**原则**：回测取数 **优先 `simulation.*` / `bt.*` 包裹**（SimClock + `bt.date`）。  
**wm-xs 兜底**：仅当糖衣盖不住时，用 `SETCURSORXS` / `AT` / `$METRIC`；行情兜底须锚 `bt.date`。禁止 `_LAST`、无锚点 kline。

## 一览

| 阶段 | 推荐（包裹） | 禁止 | 兜底（须 PIT） |
|------|--------------|------|----------------|
| selector **filter** | 裸 `$PE_TTM` / `!$IS_ST` / `$ROE_TTM` / `$BONUS_RATE_TTM`（引擎已切游标） | `_LAST` | 一般不需要 |
| selector list / rank | `simulation.*` 或切游标后 `$METRIC` | 未切游标裸读跨标的 | `SETCURSORXS(sym); $X` |
| trading / risk 跨标的 | **`simulation.pe_ttm` / `roe` / `dividend_yield` / `bar_ok` / `position_cost`** | 未切游标裸 `$PE_TTM`；猜 `pos.price` | 糖衣无该指标时：`SETCURSORXS`+`$X` 或 `AT(sym,$X)` |
| 行情 | **`bt.bar[sym].close` + `bar_ok`**；持仓兜底 `last_price` | 无日期锚的行情 | 仅 bar 缺失时：kline **锚 `bt.date`**（先 `bar_diag`） |

## 必载

trading / 调用 `pe_ttm`·`bar_ok`·`position_*` 的脚本：

```xs
xs.require("xs/simulation/lib/init.xs")
```

缺载 → lint 失败（空仓真因）。risk 至少 `trace.xs`；若用 `bar_ok` 等须 `init.xs`。

## 迷你示例

### filter（PE + ST）

```xs
return ! $IS_ST && $PE_TTM > 0 && $PE_TTM < 15
```

### trading 跨标的（包裹）

```xs
xs.require("xs/simulation/lib/init.xs")
pe := simulation.pe_ttm(sym)
if pe <= 0 || pe >= simulation.tuning("max_pe", 15) { continue }
```

### trading 原生等价（兜底，仍在 SimClock）

```xs
SETCURSORXS(STRING(sym))
pe := $PE_TTM
# 或 pe := AT(STRING(sym), $PE_TTM)
```

### 股息 / ROE

| 指标 | 包裹 | filter 裸读 |
|------|------|-------------|
| PE | `simulation.pe_ttm(sym)` | `$PE_TTM` |
| ST | — | `!$IS_ST` |
| ROE | `simulation.roe(sym)` / `roe_ttm` | `$ROE_TTM` |
| 股息率 | `simulation.dividend_yield(sym)` | `$BONUS_RATE_TTM`（口径以指标目录为准） |

## 阶段测试

写完阶段脚本后用夹具验证，见 [stage-test.md](stage-test.md)。
