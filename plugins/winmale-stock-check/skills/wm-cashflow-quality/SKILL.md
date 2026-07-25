---
name: wm-cashflow-quality
display_name: "现金流质量"
version: 1.0.4
description: 评估经营现金流与利润是否匹配。用户问「赚的是现金还是纸面利润」时使用。
---

# 现金流质量

## 何时使用

- 「现金流如何」「利润有没有兑现成现金」
- 对比同业之前，先拿本公司经营现金流质量卡片

## 前置

- Scope：`analysis:skills:run`；symbol 已确认

## 调用

`POST {WINMALE_API_BASE}/v1/skills/wm-cashflow-quality/run`

```json
{
  "symbol": "600519",
  "args": {}
}
```

## 返回要点

扁 MAP。**HTTP（双读）：** `data.ncfo_np_ratio` 等；兼容 `data.result.ncfo_*`。**无 `card` 键。**

| 字段 | HTTP（推荐） | 对用户怎么说（首次） | 含义 |
|------|--------------|----------------------|------|
| `ncfo_current` | `data.ncfo_current` | 经营现金流净额（NCFO） | 经营现金流 TTM |
| `ncfo_np_ratio` | `data.ncfo_np_ratio` | 净现比（NCFO÷净利润） | 利润含金量核心 |
| `pcf` | `data.pcf` | 市现率（PCF） | 股价相对经营现金流 |
| `ps_ncfo` | `data.ps_ncfo` | 每股经营现金流（元/股） | **不是**总量；总量看 `ncfo_current` |
| `ncfo_3y_min` | `data.ncfo_3y_min` | 近 3 年经营现金流最低水平 | 稳定性 |
| `cf_kind` | `data.cf_kind` | 现金流类型编码 | `$CF_KIND_CODE_*` 类，非分析 `$CF_KIND` |
| `annual` | `data.annual` | 年序列 | NCFO_TTM、净现比序列 |
| `sas_last` | `data.sas_last` | 最近财报 SAS | 口径定位 |

**注意**：勿按 insight 深卡去找 `card`。不返回 FCF；勿编造。重点解读净现比与 `cf_kind`。  
对用户：**禁止只甩 NCFO/PCF 代号**；遵守管家 `output-hygiene`。

## 禁止

- 用 eval 随手拼现金流勾稽冒充本卡片
- 把财务金额单位说错（以返回值为准，数量级用「亿」等换算时先确认）
