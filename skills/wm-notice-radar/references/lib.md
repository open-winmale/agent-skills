# 公告库速查（本技能主人）

域库：`sys/notice/*`（`xs.require` 链路由技能脚本加载）。**无**独立 host selector。

**数据源**：`raw__eastmoney_com.cn_all_stock_notice`（A 股）+ `hk_all_stock_notice`（港股）。美股表空 → `UNSUPPORTED_MARKET`。

## 技能已封装

| mode | 底层 |
|------|------|
| `list` | `notice.query_by_symbol`（按代码自动 CN/HK） |
| `category` | `notice.query_by_category(..., market)`；默认 cn |
| `digest` | 一次 `forecast` + `reduction` + `buyback`（`category=watch\|worth` 同） |
| `signal` | `notice.signal_has_reduction` / `signal_has_buyback`；**无 symbol → 降级 category** |

## 高频 `notice.*`

| 调用 | 用途 |
|------|------|
| `notice.query_by_symbol(sym, window, type_regex, limit)` | 单票列表（自动分表） |
| `notice.query_by_category(category, window, limit, market)` | 全市场按类；`market` 默认 cn |
| `notice.query_recent(window, type_regex, limit, market)` | 窗口检索 |
| `notice.query_on_date(date, type_regex, limit, market)` | 某日 |
| `notice.query_find` / `notice.store_find` | 自定义 filter（opts.market 或 stock_code 推断） |
| `notice.infer_market` / `notice.market_supported` / `notice.coll` | 市场分表助手 |
| `notice.signal_has_*` | 减持/增持/回购/股权激励等布尔信号 |
| `notice.type_keys()` / `notice.CATEGORIES` | 类别键（简繁正则） |
| `notice.fmt_*` / `notice.row_*` | 格式化 |

加载：`sys/notice/init.xs`（技能内已 require，eval 时需自行 require）。

**可见日**：`query_*` / `signal_*` 窗口 = `NOTICE_DATE` 命中 ∪（`timestamp` 落在窗口内且 `NOTICE_DATE ≥` 窗口起）。周末已入库、披露日挂下一交易日时可查到；重爬旧公告不会因刷新 `timestamp` 误入。`fmt_maps.announce_date` 仍为官方披露日，`available_at` 为入库时间。

## 超出时

自由标题检索、多票批量、未登记类别、PDF 全文 → 带已查范围上下文交 `wm-xs`，用 `notice.query_*` / `store_find`；**禁止**外搜新闻冒充公告。
