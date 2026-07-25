# 分红库速查（本技能主人）

域库：`sys/bonus/*`。指标层常见 `$BONUS_*` / `$DPS_*` / `$BONUS_RATE_*`（与选股字段区分：产品筛池用 `wm-screen-index`）。

## 技能已封装

| mode | 底层 |
|------|------|
| `snapshot` | `bonus.snapshot` |
| `history` | `bonus.query_list` |
| `quality` / `high_yield` | `bonus.screen_quality` / `screen_high_yield` |

## 高频 `bonus.*`

| 调用 | 用途 |
|------|------|
| `bonus.snapshot(sym)` | 单票快照（yield/payout/趋势等） |
| `bonus.query_list` / `query_last` | 分红事件历史 |
| `bonus.screen_*` | 单票门槛（quality / high_yield / danger_payout…） |
| `bonus.index_where_*` | INDEX where 砖（高股息、质量、低估…） |
| `bonus.index_field_load` / `index_fields_*` | 批量拉字段 |

加载：`sys/bonus/init.xs`。

## 超出时

全市场红利排行、行业对比、自定义 INDEX 组合 → **金融分析师** + `wm-xs-eval-guide`，优先复用 `bonus.index_where_*`，勿硬凑本卡单票 mode 冒充排行。
