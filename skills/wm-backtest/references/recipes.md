# backtest.* 宿主菜谱（eval 直调）

主轴见 [SKILL.md](../SKILL.md)：**管理面 CRUD** + **引擎日环** + [experience](experience.md) 迭代。

| 归属 | 含义 | 典型 |
|------|------|------|
| **管理·模板跑批** | L1 `from_*` + 官方 unit | `from_watchlist`、`run_custom_official_seed` |
| **引擎·自定义单元** | 自写阶段；短 inline 可 JSON；复杂 → `@xs:` / 官方 `@pack:` + **wm-xs** | **harness CHECK** → `lint` → `preview_custom` → **`run_custom`** |
| **管理·查历史** | 读进度/结果/resume | free `_backtest_*`、`resume` |
| **管理·单元迭代** | 已有 unit 改脚本再跑 | L1 **同 `unit_id` 再 `run_custom`**（默认覆盖，`mode=update`）；高级面仍可用 host write→publish |

产品侧优先 `skills/run`。关注：`from_watchlist`（默认 `backtest_market=cn`）。  
下列补全 L1 未糖衣的 host。契约：`xs/tests/capability/backtest.xs`。

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

**优先 platform_free**（OpenAPI `script_ref`，不走 skills/run EC 预检）：

```json
{"mode": "call", "script_ref": "xs/ops/_backtest_runs.xs", "args": {"list_limit": 10}, "symbol": "600519", "market": "cn"}
{"mode": "call", "script_ref": "xs/ops/_backtest_status.xs", "args": {"run_id": "..."}, "symbol": "600519", "market": "cn"}
{"mode": "call", "script_ref": "xs/ops/_backtest_summary.xs", "args": {"run_id": "..."}, "symbol": "600519", "market": "cn"}
{"mode": "call", "script_ref": "xs/ops/_backtest_deep.xs", "args": {"run_id": "...", "page_view": "audit", "page_limit": 50}, "symbol": "600519", "market": "cn"}
{"mode": "call", "script_ref": "xs/ops/_backtest_trace.xs", "args": {"run_id": "...", "page_view": "summary"}, "symbol": "600519", "market": "cn"}
```

清单：`sys/platform_free.json`。仍需 `analysis:backtest:read`。  
大结果：**先 summary/meta，再 audit/factors 分页**；翻页用返回的 `next_cursor` → `page_cursor`（见 [experience.md](experience.md) §2.2）。

深读也可 eval 直调 host（非 free 白名单时会计量/走普通 eval）：

```xs
SETXS(runs, backtest.runs(MAP{"limit": 5, "cursor": ""}))
SETXS(items, runs["items"])
if COUNT(items) == 0 {
  return MAP{"n": 0}
}
SETXS(rid, STRING(DEFAULT(items[0]["run_id"], items[0]["id"])))
SETXS(opts, MAP{"limit": 50, "cursor": ""})
return MAP{
  "run_id": rid,
  "get": backtest.run_get(rid),
  "progress": backtest.run_progress(rid),
  "metrics": backtest.run_metrics(rid),
  "equity": backtest.run_equity(rid, opts),
  "ledger": backtest.run_ledger(rid, opts),
  "holdings": backtest.run_holdings(rid, opts),
  "factors": backtest.run_factors(rid, opts),
  "trace": backtest.run_trace_summary(rid),
  "snapshot": backtest.run_snapshot(rid),
}
```

有 `analysis:backtest:event:read` 时：

```xs
backtest.events(rid, MAP{"after_seq":0,"limit":50,"type":"log","step":"risk","level":"warn"})
backtest.await_terminal(rid, MAP{"timeout_sec":300,"poll_sec":1})
```

`step` / `level` / `code` 为服务端过滤（见 [experience.md](experience.md) §2.2）。

### 2.1 一次执行的专业复盘包（历史 + 日志）

```json
{"mode":"call","script_ref":"xs/ops/_backtest_deep.xs","args":{"run_id":"...","page_limit":50},"symbol":"600519","market":"cn"}
{"mode":"call","script_ref":"xs/ops/_backtest_trace.xs","args":{"run_id":"...","page_view":"summary"},"symbol":"600519","market":"cn"}
{"mode":"call","script_ref":"xs/ops/_backtest_trace.xs","args":{"run_id":"...","page_view":"factors","page_limit":50},"symbol":"600519","market":"cn"}
```

- deep → ledger / holdings / equity（**执行历史**，分页）  
- trace → 先 `summary`，需要时再 `factors`（**过程日志**）  
打点写法见 [experience.md](experience.md) §2.1、[simulation-api.md](simulation-api.md)。

## 3. 发起跑批（计量；须确认）

`ConfigOverride` 合法字段：`universe`（**不是** `symbols`）、`start`/`end`、`script_params`、`market`=`MARKET_CN|HK|US`。  
Host 会把 `symbols`→`universe`、`cn`→`MARKET_CN`，并剥离 `reason`；仍请 Agent 直接写对。

```xs
SETXS(uid, "your_unit_id")
SETXS(started, backtest.run(uid, MAP{
  "market": "MARKET_CN",
  "universe": ARR{"600519", "000001"},
  "start": "2023-01-01",
  "end": "2024-12-31",
}))
# started: MAP{run_id, …}
SETXS(new_run, STRING(DEFAULT(started["run_id"], started["id"])))
return MAP{"run_id": new_run, "progress": backtest.run_progress(new_run)}
```

产品侧 `from_universe` / `from_strategy` / `from_watchlist` 须用户确认，预览读 `effective_config`。  
额度暂停：`backtest.run_resume(run_id)` 或技能 `action=resume`（scope `analysis:backtest:control`）。  
pause/delete → L2 / 审批，默认只挂载探测。

## 4. project_path（workspace）

```xs
# project_get 对未绑定 unit 会硬失败；默认先 path
SETXS(ppath, backtest.project_path(uid))
return ppath
```

## 5. lint + 自定义单元（代 publish）

```xs
SETXS(lint, backtest.lint("return !$IS_ST", {"file_name": "selector_filter.xs", "level": "L2", "market": "cn"}))
# 产品侧：action=lint|preview_custom|run_custom
# run_custom：project_create(unit, from)；若 UNIT_EXISTS 且 overwrite（默认 true）→ 跳过 create，写各 stage → validate → publish → run
# 默认 from=equal_weight_buy_hold；unit_id 省略则 agent_<request_id>
# lint/validate/publish 统一走池化 init EC + L2 Strict（与 /v1/analysis/xs/check 同路径）
# 完整自定义示例：skills/wm-backtest/examples/run_custom_full.json
```

Scopes：`analysis:backtest:project:write` + `workspace:write` + `workspace:publish` + `analysis:backtest:run`。  
缺 `project:write` 时宿主**不挂载** `project_create`/`project_write`/`project_publish`，调用会静默得 `nil`，随后 `project_validate` 报 not found。  
`unit_id` 已存在时 L1 默认 **覆盖迭代**（回执 `mode=update`）；仅 `overwrite=false` 才返回 `UNIT_EXISTS`。省略 `unit_id` 则自动生成新 id。

## 6. equal_weight_buy_hold

官方对照模板：宇宙内一次性等权建仓后持有（无再平衡）。`from_*` 未传 `template_unit_id` 时默认它。  
Override 示例见 §3；`universe_ref` 为空，显式 `universe` 直接生效。

### 坑

- 无 `run_id` 时不要伪造 deeplink；路径白名单 `/backtest/runs/{runId}`。  
- fork/create template 若无 `analysis:backtest:delete` 清理能力，勿留孤儿探针。  
- XS 容器字面量优先 `{}` / `[]`；`MAP{}` / `ARR{}` 仍兼容。不要写 Go 带类型字面量。
