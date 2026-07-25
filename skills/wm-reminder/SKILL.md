---
name: wm-reminder
display_name: "到时候提醒我"
version: 0.2.2
description: 列出/创建/管理我的研究提醒；支持个股、选股、榜单与任意 XS（call return 控推送）。不是调度引擎文档。
---

# 到时候提醒我

## 何时使用

- 「我有哪些提醒」
- 「跌幅到 5% 提醒我」「财报前看茅台」
- 「用一段 XS 自定义提醒条件」

## 库主人

- Host：`reminder.*`（本技能最熟练）
- 速查：[references/lib.md](references/lib.md)
- **eval 菜谱**：[references/recipes.md](references/recipes.md)
- Call 推送协议：[references/notify-protocol.md](references/notify-protocol.md)

## Action

| action | scope | 说明 |
|--------|-------|------|
| `list` | read | 列表 + quota |
| `create` | write | 真实产品字段：`type` + `name` + 配置 |
| `get` / `update` / `enable` / `cancel` | read/write | 管理已有提醒 |
| `trigger` | — | **默认禁止**（须用户确认后走宿主） |

## 创建 `type`

| type | 用途 |
|------|------|
| `pr_stock` | 个股追踪 |
| `strategy_screening` | 选股策略 |
| `pr_rank` / `market_rank` | 市赚率/行情榜 |
| `xs` | **任意 XS**；执行 call 模式，用 `return` 的 `notify` 控推送 |

自定义逻辑优先 `type=xs` + [notify-protocol](references/notify-protocol.md)。  
调度仍是 `push_control.push_time` / 事件；**无**独立 `earnings_window` 引擎（旧字段仅作文案提示）。

## SCOPE_DENIED

返回体含 **`grant_url`**（`console?appId=&action=scopes&scope=`）。对人只贴链接 +「授权后重新换 token」；禁止长篇手操。

## 调用

```json
{ "args": { "action": "list", "limit": 20 } }
```

```json
{
  "args": {
    "action": "create",
    "create": {
      "name": "PCB 跌 5%",
      "type": "xs",
      "script_content": "return MAP{\"v\":1,\"notify\":true,\"title\":\"跌幅触发\",\"body\":\"…\"}"
    }
  }
}
```

## 禁止

- 默认 `trigger`
- 代配 push_channel 密钥
- 缺权限时口述控制台路径（用 `grant_url`）
- 索引缺口改走第三方选股
