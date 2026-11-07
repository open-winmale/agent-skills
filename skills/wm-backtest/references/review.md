# 结果核对清单

专业复盘数据源与打点/拉日志工具见 [experience.md](experience.md) §2。

## 读取顺序（优先免 EC；分级，勿一次拉满）

1. `_backtest_summary.xs` — metrics（L0）  
2. `_backtest_trace.xs` `page_view=summary` — `by_code` / `top_codes`（L0）  
3. `_backtest_deep.xs` `page_view=audit` + `page_limit` — equity / **ledger** / holdings 首页；翻页用 `page_view=field`（L1）  
4. `_backtest_trace.xs` `page_view=factors` — 因子页（L1）  

可选 L2：`backtest.events(run_id, MAP{"after_seq":0,"limit":50,"type":"log","step":"risk","level":"warn"})`（event scope；step/level/code 服务端过滤）。  
分页约定见 [experience.md](experience.md) §2.2。

deeplink：`/backtest/runs/{runId}`（真实 run_id）。

## 核对表

| 检查项 | 怎么看 |
|--------|--------|
| 收益/回撤 | summary.metrics |
| 规则触发 | summary.metrics.rule_counts（`simulation.rule` + proposal.reason） |
| 是否按规则成交 | **ledger** + holdings |
| weight 是否正确 | ledger BUY；对照 trace 里的 `w` |
| 选股/风控为何 | **trace** reject / clip / 自定义 message |
| 因子是否按设计 | **factors** |
| 规则没触发 | trading 躺平；trace 无关键点 |

## 输出最低标准

历史结论 + **执行证据（ledger 或 trace）** + 成败归因 + 1～3 条可再跑改法。日志不足时改法应含「关键分支补 simulation.trace」。
