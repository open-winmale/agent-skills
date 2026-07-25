---
name: wm-dividend-quality
display_name: "股息与分红"
version: 1.0.7
description: 股息率与分红质量快照、历史与门槛判定。用户问高股息、分红是否可持续时使用。
---

# 股息分红质量

## 何时使用

- 「股息率多少」「查一下某某的股息」「适不适合红利策略」
- 需要按门槛判定 quality / high_yield

## 库主人

- 域库：`sys/bonus.*`（本技能最熟练）
- 速查：[references/lib.md](references/lib.md)
- 技能 mode：snapshot / history / quality / high_yield；全市场 INDEX 砖见 `bonus.index_where_*`

## 超出 action

```text
1) 先单票 snapshot/history/quality/high_yield
2) 全市场红利排行 / 行业对比 → role-financial-analyst + wm-xs-eval-guide，优先 bonus.index_where_*
3) 产品条件筛池（股息+估值）→ wm-screen-index，不要用本卡硬扫
4) 禁止硬凑「系统没有的排行」；禁止把 15 当 15% 传 min_yield
```

## 何时不要用 / 三态（V2）

- 单票股息质量 → 本卡  
- **全市场股息/红利排行**：若系统尚无现成排行面 → 交给 **金融分析师** 查+析，或如实说明「系统没有这类排行数据」（禁止硬凑）

## 调用

`POST {WINMALE_API_BASE}/v1/skills/wm-dividend-quality/run`

**所有 mode / 门槛参数必须放在 `args`。**

### snapshot（默认）

```json
{
  "symbol": "600519",
  "args": { "mode": "snapshot" }
}
```

### quality（门槛判定）

```json
{
  "symbol": "600519",
  "args": {
    "mode": "quality",
    "min_yield": 0.03,
    "payout_min": 0.3,
    "payout_max": 0.7
  }
}
```

### high_yield

```json
{
  "symbol": "600519",
  "args": { "mode": "high_yield", "min_yield": 0.03 }
}
```

### history

```json
{
  "symbol": "600519",
  "args": { "mode": "history", "limit": 20 }
}
```

Scope：`analysis:skills:run`。收益率/分红率参数均为**小数**（`0.03` = 3%）。

## 返回要点

- `mode`：实际执行模式
- `snapshot`：分红快照（含 yield_ttm、payout_ttm、趋势、`quote_date` 等，以返回为准）
- `quote_date` / `freshness`：收益率价格侧锚定的行情日（Q；history 行内仍用 announce/ex/pay）
- `ok` / `reasons`：quality / high_yield 是否通过及原因
- `items`：history 列表（行级含 announce / ex / pay）
- `deeplinks`：成功时**必有**解析后对象，含 `id=company.dividend`、`href`、`href_embed`、`markdown`（由 `skhub.deeplink` 生成）

## 对用户输出（硬）

任一成功 mode 后，**必须**把技能返回的 `deeplinks[].markdown`（或 `href_embed`/`href`）原样附给用户：

- 优先嵌入：`/embed/v1/company.dividend?code=…`
- 完整工作台：`/analysis?code=…&panel=dividend`
- **禁止**只贴裸 `{id,params}` 或手搓 URL

指标首次出现写中文+代号（如「股息率（Dividend Yield）」），遵守管家 `output-hygiene`。

## 禁止

- 把 `mode`/`min_yield` 放在 JSON 顶层（会被丢弃，永远走默认 snapshot）
- 把 `15` 当成 15% 传给 `min_yield`（应传 `0.15`）
- 成功取数后不给用户 `panel=dividend` 链接
