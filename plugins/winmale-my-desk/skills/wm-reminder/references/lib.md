# 提醒库速查（本技能主人）

宿主选择器：`reminder.*`（需 App overlay + reminder scopes）。

## 技能已封装

| 用途 | action |
|------|--------|
| 列出提醒 | `list` → `reminder.list` |
| 创建提醒 | `create` → `reminder.create`（产品 type + xs） |
| 详情 / 更新 / 启停 | `get` / `update` / `enable` / `cancel` |

## 高频 host API

| 调用 | 用途 | 技能是否封装 |
|------|------|--------------|
| `reminder.list(opts)` | 列表 | 是 |
| `reminder.get(id)` | 详情 | 是 |
| `reminder.quota()` | 配额 | 内部 |
| `reminder.create(spec)` | 创建 | 是 |
| `reminder.update(id, patch)` | 更新 | 是 |
| `reminder.enable` / `cancel` / `delete` | 启停删 | enable/cancel 是；delete 否 |
| `reminder.runs(id)` / `reminder.run(run_id)` | 运行记录 | 否 |
| `reminder.push_logs(...)` | 推送日志 | 否 |
| `reminder.validate(spec)` | 静态校验 | 否 |

兄弟选择器：`notification.*`、`push_channel.*`（渠道密钥配置**禁止**本技能代做）。

## SCOPE_DENIED

返回 `grant_url`（开放平台 `console?appId=&action=scopes&scope=`）。贴链接即可。

## 超出时

查 runs / delete / 确认后的 `trigger` → 经确认用 eval 调 host（须 scope）；菜谱见 [recipes.md](recipes.md)。**禁止**默认 `trigger`。
