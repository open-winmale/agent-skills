# 管理面操作清单

系统总览：[system.md](system.md)。引擎日环：[stages.md](stages.md)。

## A. 单元 CRUD

| 步骤 | L1 / host | 说明 |
|------|-----------|------|
| 列单元 | host `backtest.units` / `unit` / `catalog` | 非 L1 |
| 读脚本/路径 | `project_path` / `project_read` / `project_get` | **勿**对未绑定 unit 盲调 `project_get`（会硬失败） |
| 新建+跑 | L1 **`preview_custom` → `run_custom`** | 默认种子 `equal_weight_buy_hold`；省略 `unit_id` |
| 改阶段再跑 | `project_write` → `validate` → `publish` → `run` | 见 [recipes.md](recipes.md)；勿反复 create |
| lint | L1 `lint` | 默认 L2，与 publish 同取向 |
| 冲突 | `UNIT_EXISTS` | 换 id 或走 write 迭代 |

## B. 跑批 CRUD / 运维

| 步骤 | 通道 | EC |
|------|------|-----|
| 预览模板跑 | L1 `from_*` `confirm=false` | 计量预检可能挡 skills/run |
| 确认发起 | 同 action `confirm=true` | **计量** |
| 列表 | free `_backtest_runs.xs` 或 L1 `list` | 优先 free |
| 进度 | free `_backtest_status.xs` / L1 `status` | free |
| 指标 | free `_backtest_summary.xs` / L1 `summary` | free |
| 净值/成交/持仓 | free `_backtest_deep.xs` | free |
| trace/factors | free `_backtest_trace.xs` | free |
| 额度恢复 | L1 `resume` | 计量；需 control scope |
| pause/stop/delete | host | 非 L1；delete 常需审批 |

## C. 产品环（一次任务怎么串）

```text
Prepare（宇宙/窗口/模板或阶段脚本）
  → Lint（自定义时）
  → Preview（effective_config 必回显）
  → 用户 Confirm
  → Run（计量）
  → Monitor（status / resume）
  → Results（free summary）
  → Review（free deep/trace + 归因）
  → Improve（改脚本或 tuning）→ 回 Lint / Preview
```

## 失败分支

| 症状 | 处理 |
|------|------|
| `project_validate: not found` | 缺 `analysis:backtest:project:write` |
| `UNIT_EXISTS` | 省略 `unit_id` 或换新；迭代用 write |
| `unsupported symbol container type bool` | filter↔list/rank 返回类型错；见 stages |
| `unknown field` in script_params | 改用 `simulation.tuning` |
| 仓位远大于设定 5%/10% | 第 3 元写成了现金；应写 weight |
| pe_ttm/bar_ok 恒空 | 未 `require(init)` 或不在日环；见 simulation-api |
