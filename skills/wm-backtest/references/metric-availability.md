# 指标可用性对照表（防未来函数）

**原则**：回测取数 **优先 `simulation.*` / `bt.*` 包裹**（SimClock + `bt.date`）。  
**wm-xs 兜底**：仅当糖衣盖不住时，用 `SETCURSORXS` / `AT` / `$METRIC`；行情兜底须锚 `bt.date`。禁止 `_LAST`、无锚点 kline。

## 一览

| 阶段 | 推荐（包裹） | 禁止 | 兜底（须 PIT） |
|------|--------------|------|----------------|
| selector **filter** | 回测：裸 `$PE_TTM` / `$ROE_TTM`；**probe 估值用 `simulation.pe_ttm(symbol)`** | `_LAST` | 一般不需要 |
| selector list / rank | `simulation.*` 或切游标后 `$METRIC` | 未切游标裸读跨标的 | `SETCURSORXS(sym); $X` |
| trading / risk 跨标的 | **`simulation.pb` / `pe_ttm` / `roe` / `chg` / `rsi` / `macd` / `bar_ok` / `position_cost`** | 裸 `$PE_TTM`/`$PB_TTM`/`$RSI_14`（probe 仍是昨收）；猜 `pos.price` | 糖衣无该指标时：`SETCURSORXS`+`$X`（无价格腿 only） |
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

### trading 原生等价（兜底，仅无价格腿）

```xs
SETCURSORXS(STRING(sym))
roe := $ROE_TTM
```

估值 / 涨跌幅不要这条路径。Probe 必须 `simulation.pb` / `pe_ttm` / `chg` / `rsi` / `macd`。

### 股息 / ROE / 估值

| 指标 | 包裹 | filter 裸读 |
|------|------|-------------|
| PE / PB / PS / PR | `simulation.pe_ttm` / `pb` / `ps_ttm` / `pr` | 回测可 `$PE_TTM`；**probe 不要裸读** |
| ST | — | `!$IS_ST` |
| ROE | `simulation.roe(sym)` / `roe_ttm` | `$ROE_TTM` |
| 股息率 | `simulation.dividend_yield(sym)` | `$BONUS_RATE_TTM`（probe 随 last 须走包裹） |
| 涨跌幅 | `simulation.chg(sym, n)` / `percent` | 回测可 `$CHG_nD`；**probe 不要裸读** |

## 阶段测试

写完阶段脚本后用夹具验证，见 [stage-test.md](stage-test.md)。
