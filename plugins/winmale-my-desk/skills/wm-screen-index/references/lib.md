# 选股库速查

宿主：`screener.*`。找 field/value → **`wm-discover` domain=screener**（或本技能 `search`）；筛池 → `conditions`。

## 技能 action

| 用途 | action |
|------|--------|
| 字段/取值搜索 | `search`（同 discover screener） |
| 按名列目录 | `indicators` |
| 枚举全表 | `indicator_distinct` |
| 行业/指数元数据 | `market_meta` |
| 索引列表 | `indexes` |
| 条件筛池 | `conditions` |
| 命中约数 | `preview_count` |
| 我的策略 | `list` / `run_strategy` / `save_strategy` |

## Host（须 scope）

| 调用 | 用途 |
|------|------|
| `screener.search(q, opts)` | 名+内容搜索（distinct 进程缓存 12m） |
| `screener.indicators` / `indicator_distinct` / `market_meta` | 目录 / 枚举 / 元数据 |
| `screener.query` / `preview_count` | 筛池 / 约数 |
| `screener.run` / `screener.fetch` | 已存策略 |

辅助：`xs/skillhub/lib` deeplink / `conditions_to_where`。

未封装：策略 update/delete/fork、`nl_to_conditions`、自定义 CONFT。超出 → SKILL「超出」。  
eval 直调例子与 CAS → [recipes.md](recipes.md) / [pitfalls.md](pitfalls.md)。
