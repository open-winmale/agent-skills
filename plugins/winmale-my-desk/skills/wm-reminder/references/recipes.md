# reminder.* 宿主菜谱（eval 直调）

产品 list/create 优先本技能 `skills/run`。下列用于自定义 XS / 生命周期。  
契约来源：`scripts/xs/tests/capability/reminder.xs`。Call 推送协议：[notify-protocol.md](notify-protocol.md)；速查 [lib.md](lib.md)。

Scopes：读 `user:reminder:read`；写 `user:reminder:write`；手动触发 `user:reminder:execute`。

## 1. 列表 + 配额

```xs
SETXS(page, reminder.list(MAP{"page": 1, "page_size": 5}))
# page: MAP{items: ARR, total?, …}；item 含 sub_id / name / type
SETXS(quota, reminder.quota())
# quota: MAP{total|used|remain, …}
return MAP{"n": COUNT(DEFAULT(page["items"], ARR{})), "quota": quota}
```

## 2. 创建前 validate

```xs
SETXS(script, "return MAP{\"v\":1,\"notify\":false,\"title\":\"t\",\"body\":\"b\"}")
SETXS(ok, reminder.validate(MAP{
  "type": "xs", "name": "daily-check",
  "xs": MAP{"script_content": script},
}))
# ok: MAP{ok: bool, warnings, provenance, errors?}
# 伪造 owner_uid/app_id 会被拒：ok=false 且 errors 非空
return ok
```

## 3. create → update → cancel → enable → delete

```xs
SETXS(rid, STRING(runtime.request_id()))
SETXS(script, "return MAP{\"v\":1,\"notify\":false,\"title\":\"cap\",\"body\":\"t\"}")
SETXS(c, reminder.create(MAP{
  "type": "xs", "name": "tmp_" + SUBSTR(rid, 0, 8),
  "xs": MAP{"script_content": script},
  "reason": "eval recipe",
  "idempotency_key": "rem-c-" + rid,
}))
# c: MAP{sub_id, …}
SETXS(sid, STRING(c["sub_id"]))
reminder.update(sid, MAP{"name": "tmp_u", "reason": "u", "idempotency_key": "rem-u-" + rid})
reminder.cancel(sid, MAP{"reason": "c", "idempotency_key": "rem-can-" + rid})
reminder.enable(sid, MAP{"reason": "e", "idempotency_key": "rem-en-" + rid})
# 有 execute 时：reminder.trigger(sid) → MAP{run_id, …}；再 reminder.runs / run / push_logs
SETXS(del, reminder.delete(sid, MAP{"reason": "cleanup", "idempotency_key": "rem-d-" + rid}))
# 写操作返回常含 ok: true
return MAP{"sub_id": sid, "deleted_ok": del["ok"]}
```

测试探针请用 **`notify: false`**，避免刷推送渠道。默认 **禁止** 代用户 `trigger`（须确认 + execute scope）。

## 4. apply dry_run（不落库）

```xs
SETXS(preview, reminder.apply(MAP{
  "operations": ARR{MAP{
    "action": "create",
    "create": MAP{"type": "xs", "name": "dry", "xs": MAP{"script_content": "return MAP{\"v\":1,\"notify\":false}"}},
  }},
  "dry_run": true,
  "reason": "preview",
  "idempotency_key": "rem-dry-" + STRING(runtime.request_id()),
}))
return preview
```

## 5. targets（deep / winv2）

```xs
SETXS(t, reminder.targets())
SETXS(tref, MAP{"kind": "REMINDER_TARGET_KIND_MARKET_RANK", "ref": "gainers"})
SETXS(resolved, reminder.target_resolve(tref))
SETXS(tv, reminder.target_validate(tref, "market_rank"))
return MAP{"valid": tv["valid"], "resolved": resolved}
```
