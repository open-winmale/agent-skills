# 数值单位原则（全技能共用）

平台 XS / 选股索引 / 多数 L1 返回里的比率与金额，是**存储原始值**，不是 UI 展示串。

## 比率

- `0.04` = 4%；`0.15` = 15%；`1` = 100%
- 拼条件或写 XS 比较时：优先小数；也可用字面量 `4%`（=`0.04`）
- **禁止**把「用户说的百分之四」先当成 `4` 再除 100，或反过来再乘 100
- **禁止**对 ROE / 股息率 / 分红率 / 资产负债率使用裸整数 `15` 想表达 15%（会被当成 15 倍=1500%）

## 倍数与覆盖

- PE、PB、覆盖倍数等：真实倍数（`30`、`1.2`），不是百分数

## 金额

- 默认**元**；大数在 WHERE/XS 可用 `Y`/`W` 等字面量（见 XS 文档）
- UI「亿」是展示换算，不是存储单位

## 选股 `indicators` / discover screener 投影

`action=indicators` 与 screener search 已做 **Agent 投影**（UI 目录仍为人话刻度）：

| 字段 | 含义 |
|------|------|
| `value_scale` | `ratio` / `yi` / `wan` / `absolute` |
| `default_value` / `example_condition_value` | **存储口径**，可直接进 `scalar.value` |
| `display_unit` / `display_default_val` | UI 展示用；**禁止**原样抄进 conditions |

例：ROE `display_unit:%` + `display_default_val:15` → `value_scale:ratio` + `default_value:"0.15"`。

## Agent 纪律

- 不要猜单位；以 `value_scale` + `default_value` / 本原则 / playbook 为准
- **不要**用 `display_unit` 或裸 `display_default_val` 拼条件
- 选股细则见 `wm-screen-index/references/playbook.md` §0
- 短 XS 见 `wm-xs/references/grammar-cheatsheet.md`
