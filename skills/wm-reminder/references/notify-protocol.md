# 提醒 XS Call Notify 协议 v1

提醒 `type=xs` 在调度触发时以 **call 模式**（顶层 `return`）执行。由返回值决定是否推送。

## 合同

```text
return MAP{
  "v": 1,
  "notify": true|false,   // 必填键：false=记 run 不推；true=推送
  "title": "...",         // 可选
  "body": "...",          // 推送正文（优先于自动摘要）
  "payload": {            // 可选，兼容选股 ScreeningPayload
    "title": "...",
    "count": N,
    "rows": [ { "$SYMBOL": "...", "$NAME": "...", ... } ]
  }
}
```

## 兼容

- 若 return **无** `notify` 键，但脚本仍输出 `JSON(result)` DataView → 走旧选股摘要推送。
- `pr_stock` / `strategy_screening` / 榜单类型 **不**走本协议。
- PushControl（免打扰/日限/间隔）仍在服务端兜底。

## 示例

```xs
# 条件满足才推
SETXS(drop, ...)  # 自行计算
if drop >= 0.05 {
  return MAP{"v":1,"notify":true,"title":"跌幅≥5%","body":"..."}
}
return MAP{"v":1,"notify":false,"title":"巡检正常"}
```
