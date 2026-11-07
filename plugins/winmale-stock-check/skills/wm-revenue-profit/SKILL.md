---
name: wm-revenue-profit
display_name: "营收与利润"
version: 1.0.6
description: 追踪营收与净利润水平、同比及行业分位/份额。用户问成长性、收入利润走势、营收行业分位与份额时使用。
---

# 营收利润

## 何时使用

- 「营收利润怎么样」「近几年增长如何」「收入与净利润走势」「行业份额与分位」
- 需要年/季序列 + 行业内位置，而不是完整利润表

## 何时不要用 (When NOT to use)

- **查完整的利润表/资产负债表多期行** → 使用 `wm-statements`（财务报表 3+1）
- **查利润含金量 / 现金流** → 使用 `wm-cashflow-quality`（现金流质量卡）
- **一站式公司概况摸底** → 使用 `wm-company-card`（一站式摸底）

## 调用

**优先**用统一门面 `wm.sh run`（**禁止**手搓 `curl` / 自行拼鉴权 HTTP）：

```bash
bash .cursor/skills/wm-skillhub/scripts/wm.sh run wm-revenue-profit \
  '{}' --symbol 600519 --result
```

业务参数进 JSON（即 HTTP `args`）；标的优先 `--symbol`。
等价 HTTP 由脚本发出，Agent 勿直接拼鉴权。

```json
{"symbol": "600519", "args": {}}
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

**注意**：不直接返回毛利率/净利率字段；若用户要利润率，说明本卡以规模与增长/行业位置为主，或改用受限 eval（`wm-xs`）在沙箱内取对应指标。

## 禁止

- 把分位 `*_ind_pct` 说成「百分比占有率」时与 `*_ind_share` 混淆
- 编造本响应里没有的利润率时间序列
