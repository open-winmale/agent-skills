---
name: wm-backtest
display_name: "量化策略回测师"
version: 0.3.24
description: 把自然语言里的选股池、关注列表或交易想法收成可跑的回测任务，确认后发起，输出收益回撤等标准指标与结果解读，并指出偏差与下一轮改法。不是模拟炒股。
---

# 量化策略回测师

## 能力介绍（对人）

你说出「用哪批股票 / 我的关注 / 哪套条件、大概怎么持仓」，我帮你在历史上跑通回测、看状态与结果，并做成败归因与可再跑改法。  
不是代客下单，也不是模拟炒股软件。关注可多市场合并看；回测仍按**单一市场**（默认 A 股）。

## 试试这样问

- 「用我的关注做一趟 A 股回测，先预览再跑。」  
- 「PE&lt;15 买入、浮盈 10% 卖，近 3 年；自定义单元。」  
- 「上次回测为什么赚/亏，下一轮改哪一处再跑？」  

## 何时用 / 不用

| 用 | 不用 |
|----|------|
| 一批票 + 持仓规则，要在**历史**上验证并复盘 | 只筛票 → `wm-screen-index` |
| 自定义选股/交易/风控逻辑单元 | 只整理关注 → `wm-watchlist` |
| 查跑批状态、净值、成交、trace | Python / 第三方回测平台 |

---

## 给 Agent：系统是什么

拨测 = **两套子系统**叠在一起（基础设施库 + 对外 CRUD 包装）。不要当成「一堆无关 action」。

```text
① 管理面（对外包装围绕 CRUD）
   单元：catalog/units → project_create/write/validate/publish
         L1 自定义主糖衣 = run_custom（一键代 publish 再 run）
   跑批：run / list / status / summary / deep / trace / resume
   ConfigOverride 只改窗口·宇宙·参数，不改脚本逻辑

② 引擎面（backtest 库 = 基础设施）
   历史数据按交易日迭代
   selector(filter|list) → selector_rank → trading → risk → Go match
   库 xs/simulation/lib/* ；状态 **bt** / **book**（字段表见 simulation-api.md）
   **取数优先 simulation.* / bt.* 包裹（防未来函数）**；糖衣不够再 wm-xs PIT 兜底

③ 用法目标
   找更高胜率的逻辑与参数 → 成败归因 → 小步迭代再跑
```

写 trading/risk **前必读**：
- [xs-stage-syntax.md](references/xs-stage-syntax.md) — 阶段 XS 语法速查 / 常见报错  
- [simulation-api.md](references/simulation-api.md) — `bt`/`book` 字段白名单  
- [metric-availability.md](references/metric-availability.md) — `$METRIC` vs `simulation.*`  
- [stage-test.md](references/stage-test.md) — **阶段夹具（写完一步就测）**

**硬流程**：改完任一阶段脚本 → `xs.require("xs/simulation/test/harness.xs")` + `test_fixture` → `CHECK` → 再 lint / preview / run。  
示例：`@pack:wm-backtest/examples/xs/stage_harness/smoke.xs`。

禁止猜 `pos.cost` / `pos.price`；成本=`position_cost`/`avg_cost`；现价=`simulation.last_price` / `simulation.bar`（缺则按 `bt.date` PIT 补）。  
跨日状态用 `simulation.state_get/set`（勿 SET 改账本）。规则计数：`simulation.rule` + `WEIGHT_SKIP` / `risk_reject` → `metrics.rule_counts`。  
CN 默认基准 `index.hs300`；可用 `args.benchmark` 覆盖。

深读：[system.md](references/system.md) · [lifecycle.md](references/lifecycle.md) · [stages.md](references/stages.md) · [simulation-api.md](references/simulation-api.md) · [metric-availability.md](references/metric-availability.md) · [stage-test.md](references/stage-test.md) · [experience.md](references/experience.md) · [recipes.md](references/recipes.md) · [review.md](references/review.md)。

---

## 1. 管理面怎么用

| 对象 | 意图 | 怎么走（今日） |
|------|------|----------------|
| **单元** | 新建自定义策略 | L1 **`run_custom`**（create→write→validate→publish→run）；先 `preview_custom` |
| **单元** | 改脚本/参数再跑 | **同一 `unit_id` 再 `run_custom`**（默认覆盖，`mode=update`）；高级面仍可用 host write→publish |
| **单元** | 列官方/已发布 | host：`backtest.units` / `unit` / `catalog`（非 L1） |
| **跑批** | 模板快速开跑 | L1 `from_watchlist` / `from_universe`（默认 unit=`equal_weight_buy_hold`） |
| **跑批** | 列表/进度/指标 | free `_backtest_runs|_status|_summary.xs` 或 L1 list/status/summary |
| **跑批** | 深读/历史 | free `_backtest_deep|_trace.xs`（分级分页，见 experience §2.2） |
| **跑批** | 额度暂停恢复 | L1 `resume` |

**最重要**：灵活拨测 → **`run_custom`**（创建与同 id 迭代）。`ConfigOverride` 可改窗口/宇宙/`benchmark`/`script_params`；改阶段逻辑仍靠 write 正文（由 `run_custom` 代写）。

### 怎么读 skills/run 返回（当前版本）

HTTP 仍是 `{success, data, meta}`。XS return **摊平到 `data.*`**，同时保留完整副本 `data.result`。

| 读 | 路径 |
|----|------|
| lint 结果 | `data.lint`（或 `data.result.lint`） |
| 发起后的 run | `data.run` / `data.run_id`（若有） |
| 自定义模式 | `data.mode` = `create` \| `update` |
| 拒单计数 | summary → `metrics.rule_counts.risk_reject` |

业务参数必须在 **`args`** 里：`{"args":{"action":"run_custom",...}}`。扁平 `{"action":...}` → **`ARGS_REQUIRED`**（不再静默 list）。

硬规则：未确认禁止 `confirm=true`；`unit_id` 已存在 → `UNIT_EXISTS`（省略或换新 id）。

---

## 2. 引擎面怎么写

每个交易日：

```text
selector → selector_rank → trading → risk → match(Go)
```

| 阶段 | 模式/返回 | 要点 |
|------|-----------|------|
| selector | **filter→bool** / **list→[]symbol** | 默认种子=filter；禁止类型混用 |
| selector_rank | **[]symbol** | 禁止 `return $ROE_TTM`；list+rank 无效 |
| trading / risk | OrderProposal 列表 | 第 3 元=**weight 比例**，不是现金 |
| — | — | `selector_freq` 只管选股刷新，**≠调仓**（调仓写在 trading） |

必 `xs.require("xs/simulation/lib/init.xs")`。跨标的用 `simulation.pe_ttm` / `bar_ok`。查仿真库：`backtest.lib_read("xs/simulation/lib/…")`。  
**通用函数语法** → wm-discover / **wm-xs**。  
**阶段脚本文本**：短 inline 可写在 JSON；**复杂阶段必须**本地文件 + 引用——官方示例 `@pack:wm-backtest/examples/xs/…`，自写 `@xs:projects/backtest/<name>/….xs`（`~/.winmale/workspace/`，`wm.sh run` 展开后再 POST）。阶段内 `xs.require` 依赖库放 `scripts/` 并 **`wm.sh workspace push`**（异步拨测**不**带 request overlay）。语法起草 / check / eval 仍归 **wm-xs**，再挂 lint / preview_custom / run_custom。

契约详表：[stages.md](references/stages.md) · [simulation-api.md](references/simulation-api.md)。  
引擎权威：`winmale/biz/backtest/docs/SCRIPT_CONTEXT.md`、`BACKTEST_TDD.md`。

---

## 3. 策略迭代怎么做

目标：用历史验证找**更高胜率**的逻辑与参数，做成败归因，小步再跑。  
复盘主数据源：**执行历史（ledger/holdings）+ 过程日志（trace/factors）**。

```text
基线 → 写/改阶段 → **harness 夹具 CHECK** → lint → preview → run
  → deep（ledger）+ trace（日志）→ 归因 → 改法
```

| 环节 | 工具 |
|------|------|
| 阶段单测 | `xs/simulation/test/harness.xs` + [stage-test.md](references/stage-test.md) |
| 跑时打点 | `simulation.trace` / `reject` / `factor` / `risk_*`（须 require init） |
| 跑后拉取 | free `_backtest_deep.xs` + `_backtest_trace.xs` |

自定义单元关键分支必须打点，否则无法证明规则是否触发。详见 [experience.md](references/experience.md) §2。  
输出：历史结论 + **执行证据** + 归因 + 1～3 条可再跑改法；不构成投资建议。

---

## 例子索引

| 例子 | 归属 | 说明 |
|------|------|------|
| `examples/from_watchlist_preview.json` | 管理·模板跑批 | 关注预览 |
| `examples/run_custom_official_seed.json` | 管理·模板跑批 | 官方种子代 publish |
| `examples/lint_selector.json` | 引擎·自定义 | lint（可用 wm-xs 起草） |
| `examples/run_custom_full.json` | 引擎·自定义 | 全阶段；阶段正文 `@pack:…/xs/run_custom_full/` |
| `examples/pe_filter_trading.json` | 引擎·自定义 | PE + tuning；`@pack:…/xs/pe_filter/` |
| `examples/xs/stage_harness/smoke.xs` | 引擎·阶段单测 | 夹具：持仓∉candidates 仍可取价 |
| `examples/xs/stage_harness/trading_take_profit_check.xs` | 引擎·阶段单测 | 夹具验证 take_profit 提案 |
| `examples/xs/stage_harness/selector_rank_check.xs` | 引擎·阶段单测 | 最小 rank：按 close Top2 |
| `examples/xs/stage_harness/risk_drop_nobar_check.xs` | 引擎·阶段单测 | 最小 risk：丢无 bar 提案 |
| `examples/deep_results_eval.json` | 管理·查历史 | free 深读 |
| `examples/resume.json` | 管理·控跑批 | 额度恢复 |

```bash
bash .cursor/skills/wm-skillhub/scripts/wm.sh run wm-backtest \
  '{"action":"from_watchlist","backtest_market":"cn","confirm":false}' --result
```

---

## 附录

### Action（L1）

| action | 用途 |
|--------|------|
| `list` / `status` / `summary` | 跑批盘点（额度紧改 free） |
| `resume` | 恢复 |
| `from_universe` / `from_strategy` / `from_watchlist` | 模板跑批；先预览 |
| `lint` | 阶段脚本检查（默认 L2） |
| `preview_custom` / `run_custom` | **自定义单元主路径**；run 须 confirm |

### Scope / 计费

| 意图 | Scope / EC |
|------|------------|
| 读/深读 | `analysis:backtest:read`；free ops **免 EC** |
| from_* / run | `analysis:backtest:run`；skills/run **计量** |
| from_watchlist | + `user:watchlist:read` |
| resume | `analysis:backtest:control` |
| run_custom | + `project:write` + `workspace:write` + `workspace:publish` |

缺 `project:write` 时 `project_*` **不挂载**。

### Upgrade notes

| 版本 | 要点 |
|------|------|
| 0.3.11 | 契约/weight/UNIT_EXISTS/free deep·trace |
| 0.3.12 | 四层阅读地图 |
| 0.3.13 | 管理面 CRUD + 引擎日环；run_custom 定位 |
| **0.3.14** | 复盘工具：执行中 `simulation.trace*` 打点 + 跑后 deep/trace 拉执行历史与过程日志 |
| **0.3.15** | 结果面分级拉取：free deep/trace 支持 `page_view` / `page_limit` / `page_cursor`；先 summary 再分页 |
| **0.3.16** | `backtest.events` / event-log：服务端 `step`/`level`/`code`（及 `type`）过滤 |
| **0.3.17** | 复杂阶段 XS：`@pack:` / `@xs:` 引用（`wm.sh run` 本地展开）；examples 拆出 `.xs` |
| **0.3.18** | 本地路径对齐云 `projects/backtest/`；依赖须 `workspace push`（run_custom 无 overlay） |
| **0.3.22** | position_cost / state / bar_diag / ARGS_REQUIRED / harness / per-symbol caps |
| **0.3.23** | 引擎强制补持仓 bar；`metrics.rule_counts`；lint harness hint + 阶段最小模板；`xs-stage-syntax`；weight/手数/param 可读报错；skills/run 扁平 body → `ARGS_REQUIRED` |
| **0.3.24** | `simulation.bar`/`last_price`（PIT 补价）；`run_custom` 同 unit_id 默认覆盖（`mode`）；`args.benchmark`；`rule_counts.risk_reject*`；当前版本读 `data.*` 说明 |
