# screener.* 坑（eval）

1. **`screener.run` 第一参是 `strategy_id` 字符串**，不是 `MAP{"strategy_id":…}`（后者会变成「策略不存在」）。
2. **CAS 删除/更新**必须带 `expected_version` + `expected_revision_id`。优先一次写进 MAP 字面量；也可用 `SETXS(opts.expected_version, v)` 点路径。勿依赖未确认环境下的 `SETXS(opts["k"], v)`（旧运行时曾不写入）。
3. **`indicator_categories` / `indexes` / `market_meta`** 签名是市场字符串（`"cn"`）或省略，不要 `MAP{"market":"cn"}`。
4. **变量名不要叫 `meta`**——会与内置 `meta` selector 冲突；用 `mkt_meta`。
5. **`screener.index` / `indicator_distinct`** 部分 key/field 会上游 SYSTEM_ERROR；不确定时先挂载探测或走 discover/search。
6. **`fetch`**：`row_count==0` 时可能硬失败；先看 `run` 返回再决定是否 fetch。
7. OpenAPI 下 **`SET` 禁**；用 `SETXS` / `:=`。宿主错误有时整次 eval 失败，`# xs:goonerr` 盖不住全部。
