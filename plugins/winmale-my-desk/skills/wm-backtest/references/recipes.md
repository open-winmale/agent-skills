# backtest.* 宿主菜谱（eval 直调）

产品侧优先本技能 `skills/run`（量化策略回测师：意图→预览→确认发起→status/summary）。  
**关注列表**：`action=from_watchlist`（默认 `backtest_market=cn`；可传 `group_id` / `group_name`；预览含 `available_groups` 与各市场计数）。  
下列用于深读结果面、选模板、lint、或 action 盖不住时。  
契约来源：`scripts/xs/tests/capability/backtest.xs`。

Scopes：读 `analysis:backtest:read`；跑 `analysis:backtest:run`；`from_watchlist` 另需 `user:watchlist:read`；工程写 `analysis:backtest:project:write`；事件 `analysis:backtest:event:read`。  
**不做**默认 `template_delete` / `run_delete`（审批删）。

## 0. 从关注列表预览（产品 action）

```json
{
  "args": {
    "action": "from_watchlist",
    "backtest_market": "cn",
    "group_name": "汽车",
    "confirm": false
  }
}
```

期望字段：`watchlist.watchlist_counts`、`watchlist.market_notice`、`watchlist.available_groups`、`symbols_count`、`backtest_market`；分组时 `scope=group` + `group_id`/`group_name`；若有混仓则 `dropped_wrong_shape`。  
不传分组 = 该市场全量关注。港股/美股关注需显式 `backtest_market=hk|us`。同仓形态不符码会剔除（cn=6 位数字，hk=1–5 位，us=含字母）。

## 1. catalog / units / lint

```xs
SETXS(catalog, backtest.catalog())
SETXS(units, backtest.units())
# units: ARR；元素含 id / unit_id
SETXS(uid, STRING(DEFAULT(units[0]["id"], units[0]["unit_id"])))
SETXS(unit, backtest.unit(uid))
SETXS(lib, backtest.lib_read("xs/simulation/lib/init.xs"))
# lib: MAP{content, …}
SETXS(lint, backtest.lint("return MAP{\"ok\": true}", MAP{"file_name": "selector_filter.xs", "level": "L1"}))
return MAP{"units_n": COUNT(units), "unit_id": uid, "lint": lint}
```

## 2. 跑批列表 + 结果面

```xs
SETXS(runs, backtest.runs(MAP{"limit": 5, "cursor": ""}))
# runs: MAP{items: ARR, …}；item 含 run_id
SETXS(items, runs["items"])
if COUNT(items) == 0 {
  return MAP{"n": 0}
}
SETXS(rid, STRING(DEFAULT(items[0]["run_id"], items[0]["id"])))
return MAP{
  "run_id": rid,
  "get": backtest.run_get(rid),
  "progress": backtest.run_progress(rid),
  "metrics": backtest.run_metrics(rid),
  "equity": backtest.run_equity(rid),
  "ledger": backtest.run_ledger(rid),
  "holdings": backtest.run_holdings(rid),
  "factors": backtest.run_factors(rid),
  "trace": backtest.run_trace_summary(rid),
  "snapshot": backtest.run_snapshot(rid),
}
```

有 `analysis:backtest:event:read` 时：`backtest.events(rid, MAP{"limit": 5})`。

## 3. 发起跑批（计量；须确认）

```xs
SETXS(uid, "your_unit_id")
SETXS(started, backtest.run(uid, MAP{
  "idempotency_key": "bt-run-" + STRING(runtime.request_id()),
}))
# started: MAP{run_id, …}
SETXS(new_run, STRING(DEFAULT(started["run_id"], started["id"])))
return MAP{"run_id": new_run, "progress": backtest.run_progress(new_run)}
```

产品侧 `from_universe` / `from_strategy` 须用户确认；eval 直调同等谨慎。  
pause/control/delete → L2 / 审批，默认只挂载探测。

## 4. project_path（workspace）

```xs
# project_get 对未绑定 unit 会硬失败；默认先 path
SETXS(ppath, backtest.project_path(uid))
return ppath
```

### 坑

- 无 `run_id` 时不要伪造 deeplink；路径白名单 `/backtest/runs/{runId}`。  
- fork/create template 若无 `analysis:backtest:delete` 清理能力，勿留孤儿探针。
