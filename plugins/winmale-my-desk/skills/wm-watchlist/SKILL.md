---
name: wm-watchlist
display_name: "我的关注列表"
version: 0.3.0
description: 查看或整理我的关注列表：名称、分组、买卖点与备注、分组盘中提醒。加/删/分组用增量；整理前默认预览。统一跨市场 SoT。
---

# 我的关注列表

## 何时使用

- 「我关注了哪些」「池子里现在怎样」
- 「把茅台加进自选 / 从自选删掉 / 建分组 / 整理分组」（先预览再确认）
- 「删组 / 改名」
- 「给茅台设买点/卖点/备注」
- 「打开/关闭某分组的盘中买卖点提醒」

## 何时不要用 (When NOT to use)

- **全市场条件选股/按指标找股票** → 使用 `wm-screen-index`（条件选股）
- **单只股票的基本面/估值/多期三表事实** → 使用 `wm-company-card` / `wm-statements`
- **非自选分组的一般研究提醒**（财报窗口、自定义 XS） → 使用 `wm-reminder`

## 库主人

- Host：`watchlist.*`；归一化 / deeplink：`xs/skillhub/lib`
- 速查：[references/lib.md](references/lib.md)
- 用关注做回测 → `wm-backtest` `from_watchlist`（按 `backtest_market` 切片）

## 市场语义

- **存储**：每用户一份统一 Head；`SymbolEntry.market` 持久化；`Group.market` 可选（空=跨市场组）
- **读**：`view` 默认全量；`market=cn|hk|us` 为投影过滤
- **写**：可省略 `market`（按代码推断）；建组省略 `market` → 跨市场组；传 `cn|hk|us` → 绑定组

## 前置

- Scope：`analysis:skills:run` + `user:watchlist:read`
- 写操作另需：`user:watchlist:write`
- 分组买卖点提醒另需：`user:reminder:read` + `user:reminder:write`

## 调用

**优先**用统一门面 `wm.sh run`（**禁止**手搓 `curl` / 自行拼鉴权 HTTP）：

```bash
bash .cursor/skills/wm-skillhub/scripts/wm.sh run wm-watchlist \
  '{"action":"view"}' --result
```

### view

```json
{ "args": { "action": "view" } }
```

单市场投影：`"market": "cn"`。

**读结果**：`holdings` / `groups`（HTTP：`data.result.holdings`）。

`holdings[]` 含 `note` / `buy_price` / `sell_price`（0 = 未设）。`groups[]` 含 `alert_subscription_id`、`alert_bound`（是否已绑定分组提醒）。

### 买卖点与备注（跟股票走）

整份覆盖：未传的字段保留现值；显式 `0` / `""` 表示清除。买点须低于卖点。备注最长 80 字。

```json
{ "args": { "action": "annotate", "symbol": "600519", "buy_price": 1380, "sell_price": 1600, "note": "等回调" } }
```

只改备注：

```json
{ "args": { "action": "annotate", "symbol": "600519", "note": "中报后复核" } }
```

若该股所在分组已开提醒，会同步盘中条件。对人须再 `view`。

### 分组盘中提醒（跟分组走）

产品语义：**买卖点/备注跟股票**；**提醒开关跟分组**。订阅名 `自选·{组名}·买卖点`，`pr_stock.match_all=false`，盘中实时、一天最多三次。

**「全部自选」不能开提醒**（不要传 `group_id=all`）。先 `view` 取具体 `groups[].id`。

```json
{ "args": { "action": "alert_enable", "group_id": "<id>" } }
```

```json
{ "args": { "action": "alert_disable", "group_id": "<id>" } }
```

关闭会 Cancel 订阅，**保留绑定**，再开走 `alert_enable`。删组会停掉并删除对应订阅。

回执含 `deeplinks`（自选 + 订阅管理）；对人原样贴 `markdown`。

### 增量加票

```json
{ "args": { "action": "add", "symbols": ["601633", "00700"] } }
```

写回执在 **`apply`**（HTTP：`data.result.apply`），**不是** `result`。对用户须再 `view`。

### 增量删票（推荐；勿用 organize 删单票）

```json
{ "args": { "action": "remove", "symbols": ["601633"] } }
```

或单码：`"symbol": "601633"`。默认 `cascade=true`（同步踢出各分组）；仅主列表删、留在分组传 `"cascade": false`。

### 建分组 / 加入分组 / 移出分组 / 改名 / 删组

```json
{ "args": { "action": "group_create", "group_name": "重点关注" } }
```

一步建组并入标的（可选）：

```json
{ "args": { "action": "group_create", "group_name": "重点关注", "symbols": ["600519", "00700"] } }
```

回执**始终**含非空 `group_id`（空组亦然）；再用 `group_add` 追加标的。

**批量/单票加入分组**：

```json
{ "args": { "action": "group_add", "group_id": "<id>", "symbols": ["601633", "00700"] } }
```

```json
{ "args": { "action": "group_add", "group_id": "<id>", "symbol": "601633" } }
```

**批量/单票移出分组**（仅从指定分组移出，保留在主关注列表）：

```json
{ "args": { "action": "group_remove", "group_id": "<id>", "symbols": ["601633", "00700"] } }
```

```json
{ "args": { "action": "group_remove", "group_id": "<id>", "symbol": "601633" } }
```

**改名与删组**：

```json
{ "args": { "action": "group_rename", "group_id": "<id>", "group_name": "核心池" } }
```

```json
{ "args": { "action": "group_delete", "group_id": "<id>" } }
```

写动作回执均在 **`apply`**。

### organize（全量替换，危险）

仅用于真·整池整理。计划键名固定为 **`organize_plan`**，其中 `symbols` 是完整主关注列表，`groups` 是完整分组列表；先用 `view` 的 `holdings` / `groups` 合并成完整计划。删几只请用 `remove`。

```json
{
  "args": {
    "action": "organize",
    "organize_plan": {
      "symbols": ["600519", "00700"],
      "groups": [{"id": "<id>", "name": "核心池", "symbols": ["600519"]}]
    }
  }
}
```

大计划用 CLI 文件输入，避免命令行转义或截断：`bash .cursor/skills/wm-skillhub/scripts/wm.sh run wm-watchlist @organize_plan.json --result`（文件 JSON 仍须包在 `{"args": {...}}` 中）。

**固定流程**：先 `action=organize`（默认 `dry_run=true`）检查 `apply.diff` / `symbols_removed`；用户确认后，以同一完整计划传 `confirm=true`、`dry_run=false`。含删除时还须 `allow_removals=true`。

回执：`apply` + 顶层 `diff` / `symbols_removed`。

## 禁止

- 用残缺 `organize_plan` 当「加几只 / 删几只」导致清空或误伤池子
- 未确认就 `confirm=true` 落库
- 与「按条件选股」混淆
- 再读 `data.result.result`（已改为 `apply`）
- 对「全部自选」走 `alert_enable`（提醒只能绑具体分组）
- 把自选买卖点提醒做成 `wm-reminder` 裸 `pr_stock`（须走本技能，才能绑定 `alert_subscription_id`）
