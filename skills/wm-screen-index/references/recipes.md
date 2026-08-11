# screener.* 宿主菜谱（eval 直调）

产品筛池 / 跑策略优先本技能 `skills/run`。下列用于 **自定义 XS**、排错或 action 盖不住时。  
契约来源：`scripts/xs/tests/capability/screener.xs`。坑见 [pitfalls.md](pitfalls.md)；签名速查 [lib.md](lib.md)。算子 JSON 见 [playbook.md §4b](playbook.md)。

Scopes：读 `user:screener:strategy:read` + `user:screener:indicator:read`；筛/跑 `user:screener:run`；写 `user:screener:strategy:write`。

## 0. 国资（skills/run `action=conditions`）

无单独 `is_soe` 字段。用 `$ORG_TYPE_TAG` + `IN`：

```json
{
  "action": "conditions",
  "market": "cn",
  "top_n": 50,
  "conditions": [{
    "type": "INDICATOR",
    "field": "$ORG_TYPE_TAG",
    "operator": "IN",
    "value": { "set": { "values": ["央企", "地方国企"] } }
  }]
}
```

## 1. 列策略 + 读详情

```xs
SETXS(rows, screener.strategies(MAP{"limit": 10}))
# rows: ARR；元素含 strategy_id（或 id）、name、version、revision_id
SETXS(sid, STRING(DEFAULT(rows[0]["strategy_id"], rows[0]["id"])))
SETXS(d, screener.strategy(sid))
# d: MAP{strategy_id, name, version, revision_id, conditions, visibility, market, …}
return MAP{"n": COUNT(rows), "strategy_id": sid, "version": d["version"]}
```

## 2. 条件校验 + 现筛（preview / query）

```xs
SETXS(conds, ARR{MAP{
  "type": "INDICATOR", "field": "$ROE", "operator": "GTE",
  "value": MAP{"scalar": MAP{"value": "15"}},
}})
SETXS(v, screener.conditions_validate(conds))
# v: MAP{valid: bool, …}
SETXS(prev, screener.preview_count(MAP{"conditions": conds}, MAP{"limit": 20}))
SETXS(q, screener.query(MAP{"conditions": conds}, MAP{"limit": 5}))
return MAP{"valid": v["valid"], "preview": prev, "query": q}
```

字段名不确定 → `wm-discover` `domains=["screener"]`，或本技能 `search` / `indicators`。

## 3. 目录 / 元数据（deep）

```xs
SETXS(inds, screener.indicators(MAP{"market": "cn", "keyword": "roe", "limit": 5}))
SETXS(field0, STRING(inds[0]["field"]))
SETXS(one, screener.indicator(field0, "cn"))
# categories / indexes / market_meta 第一参是市场字符串，不要传 MAP
SETXS(cats, screener.indicator_categories("cn"))
SETXS(mkt_meta, screener.market_meta("cn"))
SETXS(breadth, screener.market_breadth("cn"))
return MAP{"field": field0, "cats_n": COUNT(cats)}
```

## 4. 创建 → 跑 → CAS 删除（须 write；跑须 run）

```xs
SETXS(rid, STRING(runtime.request_id()))
SETXS(conds, ARR{MAP{
  "type": "INDICATOR", "field": "$ROE", "operator": "GTE",
  "value": MAP{"scalar": MAP{"value": "15"}},
}})
SETXS(c, screener.strategy_create(MAP{
  "name": "tmp_" + SUBSTR(rid, 0, 8),
  "visibility": "private", "market": "cn",
  "conditions": conds,
  "reason": "eval recipe",
  "idempotency_key": "sc-create-" + rid,
}))
# c: MAP{strategy_id, version, revision_id, …}
SETXS(sid, STRING(c["strategy_id"]))
SETXS(runres, screener.run(sid, MAP{"limit": 5, "idempotency_key": "sc-run-" + rid}))
# run 第一参是 strategy_id 字符串；返回 result_ref / row_count
SETXS(d, screener.strategy(sid))
SETXS(del, screener.strategy_delete(sid, MAP{
  "expected_version": FLOAT(d["version"]),
  "expected_revision_id": STRING(d["revision_id"]),
  "reason": "cleanup",
  "idempotency_key": "sc-del-" + rid,
}))
# del: MAP{deleted: true, strategy_id}
return MAP{"sid": sid, "deleted": del["deleted"], "row_count": runres["row_count"]}
```

`fetch` 仅在 `row_count > 0` 且有 `result_ref` 时调用。
