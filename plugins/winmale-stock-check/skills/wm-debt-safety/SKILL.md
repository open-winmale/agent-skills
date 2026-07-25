---
name: wm-debt-safety
display_name: "负债安全"
version: 1.0.2
description: 检视资产负债率、有息负债与偿债比率。用户问杠杆、偿债能力或会不会爆雷时使用。
---

# 负债安全

## 何时使用

- 「负债高吗」「有息负债占比」「短期偿债能力」
- 需要杠杆与流动性一览，而不是完整资产负债表逐行

## 调用

`POST {WINMALE_API_BASE}/v1/skills/wm-debt-safety/run`

```json
{
  "symbol": "600519",
  "args": {}
}
```

Scope：`analysis:skills:run`。

## 返回要点

| 字段 | 含义 |
|------|------|
| `tl_current` | 资产负债率（当前） |
| `tl_yoy` | 资产负债率同比变化 |
| `tl_ind_avg` | 同行业 3 年平均资产负债率 |
| `tl_3y_trend` | 近 3 年资产负债率趋势标签 |
| `ibd_rate` | 有息负债率 |
| `current_ratio` / `quick_ratio` / `cash_ratio` | 流动 / 速动 / 现金比率 |
| `icr` | 利息保障倍数 |
| `cf_tcl` | 经营现金流对总负债覆盖 |
| `annual` | 年序列（负债率、有息负债率等） |

解读时同时对照 `tl_ind_avg`，避免只报绝对水平。

## 禁止

- 夸大「绝对安全/必爆雷」；用数据讲边际
- 顶层乱塞参数（本技能只需 `symbol` + 空 `args`）
