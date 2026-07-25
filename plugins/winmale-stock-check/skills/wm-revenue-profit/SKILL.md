---
name: wm-revenue-profit
display_name: "营收与利润"
version: 1.0.2
description: 追踪营收与净利润水平、同比及行业分位/份额。用户问成长性、收入利润走势时使用。
---

# 营收利润

## 何时使用

- 「营收利润怎么样」「近几年增长如何」
- 需要年/季序列 + 行业内位置，而不是完整利润表

## 调用

`POST {WINMALE_API_BASE}/v1/skills/wm-revenue-profit/run`

```json
{
  "symbol": "600519",
  "args": {}
}
```

Scope：`analysis:skills:run`。

## 返回要点

| 字段 | 含义 |
|------|------|
| `tr_current` / `np_current` | 营收 TTM / 净利润 TTM |
| `tr_yoy` / `np_yoy` | 同比 |
| `annual` | 年序列（营收、利润及增速） |
| `quarterly` | 近季序列（单季同比等） |
| `ind_name` | 行业名 |
| `tr_ind_avg` / `np_ind_avg` | 行业均值参考 |
| `tr_ind_pct` / `np_ind_pct` | 行业分位 |
| `tr_ind_share` / `np_ind_share` | 行业份额 |
| `mv` / `close` / `percent` | 市值与行情辅助 |

**注意**：不直接返回毛利率/净利率字段；若用户要利润率，说明本卡以规模与增长/行业位置为主，或改用受限 eval（`wm-xs-eval-guide`）在沙箱内取对应指标。

## 禁止

- 把分位 `*_ind_pct` 说成「百分比占有率」时与 `*_ind_share` 混淆
- 编造本响应里没有的利润率时间序列
