---
name: wm-watchlist
display_name: "我的关注列表"
version: 0.2.2
description: 查看或整理我的关注列表：返回公司名称、分组与关键指标快照，不是裸代码列表。加/删用增量；整理前默认预览。统一跨市场 SoT。
---

# 我的关注列表

## 何时使用

- 「我关注了哪些」「池子里现在怎样」
- 「把茅台加进自选 / 从自选删掉 / 建分组 / 整理分组」（先预览再确认）
- 「删组 / 改名」

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

## 调用

`POST {WINMALE_API_BASE}/v1/skills/wm-watchlist/run`

### view

```json
{ "args": { "action": "view" } }
```

单市场投影：`"market": "cn"`。

**读结果**：`holdings` / `groups`（HTTP：`data.result.holdings`）。

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

### 建分组 / 加入 / 改名 / 删组

```json
{ "args": { "action": "group_create", "group_name": "重点关注" } }
```

```json
{ "args": { "action": "group_add", "group_id": "<id>", "symbol": "601633" } }
```

```json
{ "args": { "action": "group_rename", "group_id": "<id>", "group_name": "核心池" } }
```

```json
{ "args": { "action": "group_delete", "group_id": "<id>" } }
```

写动作回执均在 **`apply`**。

### organize（全量替换，危险）

仅用于真·整池整理。删几只请用 `remove`。正式提交：`confirm=true` 且 `dry_run=false`；含删除时还须 `allow_removals=true`。

回执：`apply` + 顶层 `diff` / `symbols_removed`。

## 禁止

- 用残缺 `organize_plan` 当「加几只 / 删几只」导致清空或误伤池子
- 未确认就 `confirm=true` 落库
- 与「按条件选股」混淆
- 再读 `data.result.result`（已改为 `apply`）
