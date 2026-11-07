# 关注列表库速查（本技能主人）

宿主选择器：`watchlist.*`。归一化 / deeplink：`xs/skillhub/lib`（`skhub.norm_symbol*`、`skhub.deeplink("watchlist")`）。

## 技能已封装

| 用途 | action |
|------|--------|
| 查看（默认全量；可投影） | `view` → `snapshot` + 指标（含买卖点/备注、分组 `alert_bound`） |
| 增量加票 | `add` → `batch_add` |
| 增量删票（默认 cascade） | `remove` → `batch_remove` |
| 建组 / 加组 / 改名 / 删组 | `group_create` / `group_add` / `group_rename` / `group_delete` |
| 买卖点 + 备注 | `annotate` → `set_annotation` |
| 分组盘中提醒开关 | `alert_enable` / `alert_disable`（绑 `reminder.*` + `group_set_alert`） |
| 全量整理（危险） | `organize` → `apply`（默认 dry_run） |

## 市场

- 统一 SoT；写可省略 `market`（推断）；建组省略 = 跨市场组
- `view` / `snapshot` 传 `cn|hk|us` 为投影过滤

## 高频 host API

| 调用 | 用途 | 技能 |
|------|------|------|
| `watchlist.snapshot(opts)` | 快照 | view |
| `watchlist.batch_add` / `add` | 加票 | add |
| `watchlist.batch_remove` / `remove` | 删票 | remove |
| `watchlist.group_*` | 分组 CRUD | 部分 |
| `watchlist.apply(plan)` | 事务落库 | organize |
| `watchlist.contains` / `notes` / `tags` / `set_note` / `set_tags` | 备注标签 | 部分（备注走 annotate） |
| `watchlist.set_annotation` | 买卖点+备注整份覆盖 | annotate |
| `watchlist.group_set_alert` | 绑定/解绑分组提醒订阅 | alert_enable / alert_disable |
| `watchlist.quota` | 配额 | 内部 |

## 超出时

- 「只删某几只」→ **`action=remove`**（须确认）；勿用残缺 organize
- 「关注池里再按条件筛」→ 先 `view` 取 symbols，再 `wm-xs`（CONFT/INDEX）；**不要**假装 watchlist 自带选股引擎
- 「用我的关注做回测」→ **`wm-backtest` `from_watchlist`**（默认 A 股 `backtest_market=cn`；预览会说明跨市场已切开）
- 「非自选分组的一般提醒」→ **`wm-reminder`**；自选买卖点提醒必须走本技能 `alert_enable`

eval 直调完整例子 → [recipes.md](recipes.md)。
