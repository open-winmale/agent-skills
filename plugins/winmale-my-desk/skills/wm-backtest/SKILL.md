---
name: wm-backtest
display_name: "量化策略回测师"
version: 0.3.3
description: 把自然语言里的选股池、关注列表或交易想法收成可跑的回测任务，确认后发起，输出收益回撤等标准指标与结果解读，并指出偏差与下一轮改法。不是模拟炒股。
---

# 量化策略回测师

## 能力介绍（对人）

你说出「用哪批股票 / 我的关注 / 哪套条件、大概怎么持仓」，我帮你：

1. 收成一份说得清的回测任务（宇宙、模板、关键约束）  
2. **先预览，你点头后再跑**（会计量）  
3. 盯进度，用收益、回撤等指标把结果讲明白  
4. 标出已知局限，并给 1～3 条可再跑的改进建议  

不是代客下单，也不是模拟炒股软件。

### 关注列表怎么接回测（重要）

- App 里关注可以**合并看**多市场；回测暂时仍按 **单一市场** 跑。  
- 默认用 **A 股（`backtest_market=cn`）** 里的关注标的；港股/美股不会悄悄混进同一趟。  
- 预览里会写清：关注里 cn/hk/us 各有多少只、本次用了哪边、其它市场跳过几只。  
- 同仓若混入形态不符代码（如 cn 仓里的 5 位港股码），会剔除并在 `dropped_wrong_shape` 列出。  
- 若要回测港股/美股关注，请明确说，并设 `backtest_market=hk` 或 `us`。

## 擅长

- 策略 / 股票池 / **我的关注** 历史表现回测  
- 跑批进度与结果解读  
- 选股结果衔接到回测（须确认）  

## 试试这样问

- 「用我的关注列表做一趟 A 股回测，先预览再跑。」  
- 「用关注里『汽车』分组做回测，先预览。」  
- 「用我刚筛出来的高 ROE 池子，等权月调仓，从 2023 看到 2024，先告诉我你会怎么回测。」  
- 「我保存的那个选股策略，看一下这三年历史表现怎么样。」  
- 「最近一次回测收益回撤怎样，主要赚亏在哪，下一轮怎么改？」  

## 何时不要用

- 只想按条件筛股票 → `wm-screen-index`  
- 只整理关注、不加回测 → `wm-watchlist`  
- 单票基本面 / 估值一页纸 → 对应公司卡技能  
- 要写 Python 回测脚本或第三方回测平台 → 超出本产品  

---

## 给 Agent

Host 库主人：`backtest.*`；关注宇宙内置读 `watchlist.*`（须 `user:watchlist:read`）。  
深读 surface → [references/recipes.md](references/recipes.md)。

### 工作流

```text
1) 收意图 → symbols | strategy_id | from_watchlist、区间/调仓、模板
2) 若来自关注：拉分组列表；有 group_id|group_name 则取该组，否则全量 snap；按 backtest_market（默认 cn）+ 形态过滤；预览带 available_groups
3) 对齐 template_unit_id；缺则 list/units 问用户
4) confirm=false 预览 → 白话复述任务与市场范围
5) 用户确认 → confirm=true 发起（analysis:backtest:run）
6) status / summary；需要时 equity·ledger·holdings·factors·trace
7) 人话解读 + 已知偏差 + 1～3 条可执行改法
```

未确认禁止 `confirm=true`。pause / delete 默认不做（L2）。

### Action

| action | 用途 |
|--------|------|
| `list` | 我的跑批 |
| `status` | 进度（要 `run_id`） |
| `summary` | 核心指标（要 `run_id`） |
| `from_universe` | 一批股票 → 历史表现（先预览） |
| `from_strategy` | 已存选股 → 历史表现（先预览） |
| `from_watchlist` | **我的关注**（全量或分组）→ 历史表现（先预览；默认 `backtest_market=cn`） |

### 调用

`POST {WINMALE_API_BASE}/v1/skills/wm-backtest/run`，参数进 `args`。

```json
{ "args": { "action": "list", "limit": 10 } }
```

```json
{
  "args": {
    "action": "from_watchlist",
    "backtest_market": "cn",
    "group_name": "汽车",
    "template_unit_id": "",
    "confirm": false
  }
}
```

可选：`group_id` 或 `group_name`/`group`（该 `backtest_market` 下的分组；不传则全量关注）。  
预览 `watchlist.available_groups` 列出可选分组。  
`from_universe` 同样认 `backtest_market`（默认 `cn`）。

确认后补齐 `template_unit_id` 且 `confirm: true`。

### 输出

- 发起前：宇宙 + **市场** + 模板 + 将计量；`from_watchlist` 须带 `watchlist.watchlist_counts` / `market_notice` / `available_groups`；分组时还有 `group_id`/`group_name`；必要时 `dropped_wrong_shape`  
- 跟踪：进度；真实 `run_id` deeplink（`/backtest/runs/{runId}`）  
- 解读：收益/回撤；改进建议可执行  

### 禁止

- 未确认就跑；伪造 `run_id` deeplink  
- 把多市场关注默默混进同一趟回测而不说明  
- 与模拟炒股文案混淆；嵌进 `wm-screen-index` 单次 run  
