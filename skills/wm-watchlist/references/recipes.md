# watchlist.* 宿主菜谱（eval 直调）

产品 view/add/remove/organize 优先本技能 `skills/run`。下列用于自定义 XS。  
契约来源：`scripts/xs/tests/capability/watchlist.xs`。速查 [lib.md](lib.md)。

Scopes：读 `user:watchlist:read`；写 `user:watchlist:write`。  
**变量名勿用 `market`**（与内置冲突）→ 用 `wl_market`。

## 1. 快照 + 配额

```xs
SETXS(wl_market, "cn")
SETXS(snap, watchlist.snapshot(wl_market))
# snap: MAP{owner_uid, market, revision, symbols, groups, updated_at, …}
SETXS(quota, watchlist.quota())
# quota: MAP{max_stocks, max_groups, max_stocks_per_group, …}
return MAP{"rev": snap["revision"], "n": COUNT(snap["symbols"]), "quota": quota}
```

## 2. 查询面

```xs
SETXS(wl_market, "cn")
SETXS(syms, watchlist.symbols(wl_market))
SETXS(groups, watchlist.groups(wl_market))
# contains / groups_for / notes / tags
CHECK(watchlist.contains("__nope__", wl_market) == false, "missing")
if COUNT(syms) > 0 {
  SETXS(s0, STRING(syms[0]))
  return MAP{
    "in": watchlist.contains(s0, wl_market),
    "groups_for": watchlist.groups_for(s0, wl_market),
    "note": watchlist.notes(s0, wl_market),
    "tags": watchlist.tags(s0, wl_market),
  }
}
return MAP{"n": 0}
```

## 3. apply dry_run（整理预览，不落库）

```xs
SETXS(wl_market, "cn")
SETXS(rev, INT(watchlist.snapshot(wl_market)["revision"]))
SETXS(preview, watchlist.apply(
  MAP{
    "symbols": ARR{MAP{"symbol": "600519", "note": "preview", "tags": ARR{"x"}}},
    "groups": ARR{},
  },
  MAP{
    "market": wl_market,
    "dry_run": true,
    "expected_revision": rev,
    "reason": "preview",
    "idempotency_key": "wl-dry-" + STRING(runtime.request_id()),
  },
))
# preview: MAP{dry_run: true, diff, head{revision, …}, …}
# dry_run 后 revision 不变
return preview
```

## 4. 增量写（每步刷新 revision）

```xs
SETXS(wl_market, "cn")
SETXS(rid, STRING(runtime.request_id()))
SETXS(rev, INT(watchlist.snapshot(wl_market)["revision"]))
SETXS(r, watchlist.add("688001", MAP{
  "market": wl_market, "note": "tmp", "tags": ARR{"cap"},
  "expected_revision": rev,
  "reason": "add", "idempotency_key": "wl-add-" + rid,
}))
# 写返回常含 head（新 revision / symbols / groups）
# 后续 set_note / set_tags / batch_add / group_* / remove 同理：先 snapshot 取 rev
return r
```

## 5. apply 还原基线

写探针前保存 `baseline = snapshot`；结束后：

```xs
SETXS(rev, INT(watchlist.snapshot(wl_market)["revision"]))
SETXS(restore, watchlist.apply(
  MAP{"symbols": baseline["symbols"], "groups": baseline["groups"]},
  MAP{
    "market": wl_market, "dry_run": false,
    "expected_revision": rev,
    "reason": "restore", "idempotency_key": "wl-restore-" + rid,
  },
))
return restore
```

### 坑

- 每次写带 **`expected_revision`**；失败后必须重新 `snapshot`，勿沿用旧 rev。  
- OpenAPI 下 **stale revision 整次 eval 失败**（goonerr 盖不住）。  
- `statement if` 块内首次 `SETXS` 有块作用域；跨块累加用外层变量或 `IF()` 表达式。  
- 统一 SoT：写可省略 `market`；`group_create` 省略 market → 跨市场组；读可投影。
