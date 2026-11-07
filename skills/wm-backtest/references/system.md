# 拨测系统：管理面 + 引擎面

权威实现：`winmale/biz/backtest/`。文档索引：`biz/backtest/docs/README.md`、`SCRIPT_CONTEXT.md`、`BACKTEST_TDD.md`、`IMPLEMENTATION.md`。

## 一句话

| 面 | 角色 |
|----|------|
| **管理面** | 拨测**单元**与**跑批**的 CRUD、状态、历史、发布与发起 |
| **引擎面** | 历史日频状态机：阶段 XS + Go 撮合/账本；`simulation.*` / `bt.*` |

对外 L1（`wm_backtest.xs`）是管理面糖衣；**自定义逻辑的主路径是 `run_custom`**。引擎本身是基础设施级库，不是「再包一层神秘运行时」。

## 管理面

### 单元（Unit）SoT

| 来源 | 路径 | 可编辑 |
|------|------|--------|
| 官方 | `scripts/xs/backtest/<unit_id>/`（如 `equal_weight_buy_hold`） | 否（只读种子） |
| 用户 | workspace `projects/backtest/<unit_id>/` + Mongo 指针 | `project_write` → `project_publish` |

绑定 workspace 后**不要**用 legacy `template_update` / `template_sync_config` 旁路改脚本。

### 单元生命周期

```text
project_create(from?) → project_write(stage, xs) → project_validate / lint
  → project_publish（L2 严格；OpenAPI run 须已发布）
  → backtest.run(unit_id, ConfigOverride?)
```

L1 **`run_custom`** = 上列一键糖衣。迭代同一 unit：write→validate→publish→run；**勿反复 create**（`UNIT_EXISTS`）。

### 跑批生命周期

```text
queued → running → (pause) → terminal
读：runs / run_get / progress / metrics / equity / ledger / holdings / factors / trace
控：resume（L1）；pause/stop/cancel 走 host（非 L1）
```

免 EC：`xs/ops/_backtest_runs|_status|_summary|_deep|_trace.xs`。

### ConfigOverride vs 改脚本

| 通道 | 能改 | 不能改 |
|------|------|--------|
| `ConfigOverride` | 窗口 start/end、universe、market、已声明 script_params、risk 限额… | 阶段脚本正文 |
| `project_write` + publish | selector / rank / trading / risk 正文 | — |

Host 会把 `symbols`→`universe`、`cn`→`MARKET_CN`；Agent 仍应直接写对。

## 引擎面

### 分工

| 层 | 职责 |
|----|------|
| **XS（Alpha）** | 选谁、怎么排、意向买卖、软风控 |
| **Go（Execution）** | 日历、除权、T+1、费用、硬限额、撮合、NAV、审计 |

### 日环（每个交易日）

```text
账本日初 / 排队撮合（视 execution_timing）
  → 公司行为
  → selector（按 selector_freq 刷新；否则 bt.candidates sticky）
  → selector_rank（可选）
  → trading → [group_label?] → risk → match
  → 盯市 / 净值 / trace
```

详见 [stages.md](stages.md)。状态注入：`bt.*`、`book`（脚本只读，禁止 SET）。库：[simulation-api.md](simulation-api.md)。

### 写脚本

复杂逻辑用 **wm-xs** 起草 → `lint` → 管理面挂上 unit。禁止回测脚本里用 `_LAST` / 实盘 INDEX 捷径；用 `$METRIC` + PIT（`bt.date` / `simulation.hist_pct`）。

## 何时用本系统

- 要把「股票池 + 规则」在**历史区间**跑通并复盘  
- 要自定义阶段逻辑或迭代参数  

不是：只筛票、只盯盘、非本引擎回测。
