# 公告库速查（本技能主人）

域库：`sys/notice/*`（`xs.require` 链路由技能脚本加载）。**无**独立 host selector。

## 技能已封装

| mode | 底层 |
|------|------|
| `list` | `notice.query_by_symbol` |
| `category` | `notice.query_by_category` |
| `signal` | `notice.signal_has_reduction` / `signal_has_buyback` |

## 高频 `notice.*`

| 调用 | 用途 |
|------|------|
| `notice.query_by_symbol(sym, window, type_regex, limit)` | 单票列表 |
| `notice.query_by_category(category, window, limit)` | 全市场按类 |
| `notice.query_recent(window, type_regex, limit)` | 窗口检索 |
| `notice.query_on_date(date, type_regex, limit)` | 某日 |
| `notice.query_find` / `notice.store_find` | 自定义 filter（底层 Mongo） |
| `notice.signal_has_*` | 减持/增持/回购/股权激励等布尔信号 |
| `notice.type_keys()` / `notice.CATEGORIES` | 类别键 |
| `notice.fmt_*` / `notice.row_*` | 格式化 |

加载：`sys/notice/init.xs`（技能内已 require，eval 时需自行 require）。

## 超出时

自由标题检索、多票批量、未登记类别、PDF 全文 → 带已查范围上下文交 `wm-xs-eval-guide`，用 `notice.query_*` / `store_find`；**禁止**外搜新闻冒充公告。
