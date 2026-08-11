---
name: wm-debt-safety
display_name: "负债安全"
version: 1.0.6
description: 检视资产负债率、有息负债与偿债比率。用户问杠杆、偿债能力、债务风险或会不会爆雷时使用。
---

# 负债安全

## 何时使用

- 「负债高吗」「有息负债占比」「短期偿债能力」「债务风险」「会不会爆雷」
- 需要杠杆与流动性一览，而不是完整资产负债表逐行

## 何时不要用 (When NOT to use)

- **常规公司摸底/初印象** → 使用 `wm-company-card`（一站式全景卡片已包含核心负债指标，不要额外扇出本卡）
- **完整资产负债表多期查看** → 使用 `wm-statements`

## 调用

**优先**用统一门面 `wm.sh run`（**禁止**手搓 `curl` / 自行拼鉴权 HTTP）：

```bash
bash .cursor/skills/wm-skillhub/scripts/wm.sh run wm-debt-safety \
  '{}' --symbol 600519 --result
```

业务参数进 JSON（即 HTTP `args`）；标的优先 `--symbol`。
等价 HTTP 由脚本发出，Agent 勿直接拼鉴权。

```json
{"symbol": "600519", "args": {}}
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
