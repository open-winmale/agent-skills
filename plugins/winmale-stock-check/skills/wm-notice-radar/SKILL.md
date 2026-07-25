---
name: wm-notice-radar
display_name: "公告搜索"
version: 1.1.1
description: 查询 A 股公司公告，或按类别/减持回购信号扫描。用户问公告、业绩预告、减持回购、全市场公告汇总时使用。
---

# 公告搜索

## 何时使用

- 「最近有什么公告」「有没有业绩预告」
- 「是否出现减持/回购信号」
- 「最近 N 天全市场公告汇总 / 哪些值得关注」（**未点名单票**）

## 库主人

- 域库：`sys/notice.*`（本技能最熟练；无独立 host selector）
- 速查：[references/lib.md](references/lib.md)
- 技能 mode：`list` / `category` / `signal`；更细查询用 notice.query_* / store_find

## 超出 action

```text
1) 先 list / category / signal
2) 自由标题、多票、未登记类别、某日全量 → 带已用 window/category 上下文交 wm-xs-eval-guide，复用 notice.*
3) 禁止外搜新闻；禁止把全市场做成「我的关注」汇总
```

## 范围选择（极易错）

| 用户说法 | 正确做法 | 禁止 |
|----------|----------|------|
| 某公司最近公告 | `mode: list` + `symbol` | — |
| **全市场 / 最近几天公告报告 / 值得关注的公告**（未说「我的关注」） | `mode: category`（可多类别）+ `window`（如 `7d`） | **禁止**默认先拉 `wm-watchlist` 再逐票 list |
| 「我的关注 / 自选里有什么大事」 | 关注列表 Role + watchlist，再按成分查公告 | 勿说成「全市场」 |

WorkBuddy 真实踩坑：用户要「最近7天公告报告、中翻中」，Agent 却汇总了关注列表——**范围错误，一票否决。**

## 调用

`POST {WINMALE_API_BASE}/v1/skills/wm-notice-radar/run`

**`mode` / `window` / `limit` / `category` / `signal` 一律进 `args`。**

### 单票公告列表（默认 list）

```json
{
  "symbol": "600519",
  "args": { "mode": "list", "window": "1m", "limit": 20 }
}
```

### 按类别扫描（全市场，不需要特定公司）

```json
{
  "args": {
    "mode": "category",
    "category": "forecast",
    "window": "7d",
    "limit": 50
  }
}
```

用户要「最近7天值得关注」时：至少扫业绩预告类，并视需要补回购/减持等类别；用白话中文写报告，突出主题与个股线索，**勿编造未返回的财务数字**。

### 事件信号（减持 / 回购）

```json
{
  "symbol": "600519",
  "args": {
    "mode": "signal",
    "signal": "reduction",
    "window": "1m"
  }
}
```

`signal` 仅支持：`reduction` | `buyback`（其它值按 reduction 处理）。  
`window` 如 `1m`、`7d`（以服务端约定为准）。  
`category` 默认 `forecast`（业绩预告类）；其它类目以 notice 体系为准。

Scope：`analysis:skills:run`。

## 返回要点

| mode | 关键字段 |
|------|----------|
| `list` | `items` 公告列表（条目含 `date` / `announce_date`） |
| `category` | `items` + `category`/`window`（同上，A 只挂条目） |
| `signal` | `hit` + `evidence[]`（证据条目含 `announce_date`，非函数名字符串） |

**时间口径**：公告日 **A** 只挂在条目/证据上，**不**进市场级 `freshness` / `qi_index_quote`。

**注意**：信号模式只覆盖减持/回购，不是「任意重大事项雷达」。定期报告全文检索能力有限时，如实说明，勿承诺「所有分红送配公告全能搜」。

## 禁止

- 参数放顶层导致 mode 失效
- 把 signal 结果说成法律结论（仅作线索）
- **把「全市场公告汇总」做成「关注列表公告汇总」**
- 为凑报告去外搜新闻或编造业绩数字
