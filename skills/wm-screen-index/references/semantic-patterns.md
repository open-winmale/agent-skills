# 选股指标语义撮合手册（Agent）

自然语言选股意图 → 索引列。拼 `conditions` 前先读本页范式，再用 `action=indicators` 核对真实 field。

更全的单位 / alias / 缺口交接见 [playbook.md](playbook.md)；字段分片见 [fields/_index.md](fields/_index.md)。

---

## 1. 连续性 / 稳定底线 → `_MIN`

用户说 **「连续 N 年」「近 N 年一直」「不低于」** → 映射 **`_MIN`（窗口内最小值）**。

| 口语 | 常用 field（须再经 indicators 确认） |
|------|--------------------------------------|
| 连续 3/5/10 年分红/股息率不低于 X | `$BONUS_{3\|5\|10}Y_MIN_LAST` / `$BONUS_RATE_{3\|5\|10}Y_MIN_LAST` |
| 连续 N 年盈利/扣非不破底 | `$CUR_IND_DPPR_3Y_MIN_LAST` / `$CUR_IND_NP_5Y_MIN_LAST` > 0 等 |
| 连续 N 年 ROE 保持高水平 | `$CUR_IND_ROE_3Y_MIN_LAST` / `$CUR_IND_ROE_DPPR_5Y_MIN_LAST` |

索引无「连续次数 COUNT」；`_MIN` 是代理口径，**须向用户披露**。  
**仍属本技能**：能映射到 `_MIN`/`_AVG`/`_TREND` 的「连续 N 年…不低于」→ 直接 `conditions`，**勿**误交 xs-eval。

---

## 2. 中枢 / 均值 → `_AVG`

用户说 **「平均」「中枢」「长期处于」** → **`_AVG`**。

- 近 5 年平均股息率 > 3% → `$BONUS_RATE_5Y_AVG_LAST` ≥ `0.03` 或 `3%`
- 长期毛利率高于 25% → `$CUR_IND_GMR_5Y_AVG_LAST` / `_10Y_` 等

---

## 3. 趋势 / 方向 → `_TREND` / `_YOY_3Q`

用户说 **「趋势向上」「连续改善」「三季度连增」** → **`_TREND`** / **`_YOY_3Q_TREND`**。

- 分红/股息趋势递增 → `$BONUS_3Y_TREND_LAST` / `$BONUS_RATE_*_TREND_LAST`
- 净利润连续三季度改善 → `$CUR_IND_NP_YOY_3Q_TREND_LAST` 等

---

## 4. 同业相对比较

「高于行业」「行业前 20%/50%」→ `$CUR_IND_*` 分位/份额列，或 fieldCompare（见 playbook）。

- 市值行业分位：`$CUR_IND_MV_PCT_LAST`
- ROE/净利率/毛利率行业分位：`$CUR_IND_ROE_PCT_LAST` 等  

未提「行业」时，优先公司自身字段，勿默认 `$CUR_IND_*`。

---

## 5. 现金流与偿债（易错）

| 意图 | 方向 |
|------|------|
| 现金流画像 / 八型 | `$CF_KIND_CODE_{3\|5\|10}Y_LAST`（枚举；先 indicators/distinct） |
| 有效年数 | `$CF_KIND_VALID_*_LAST` |
| 经营现金流/流动负债 | `$CF_TCL_RATIO_LAST` |
| 现金偿债 | `$CASH_TO_DEBT_LAST` 等 |

**每股** `$PS_NCFO_*` ≠ **总量** `$NCFO_*`。

---

## 6. 分类速查（入口，非全表）

| 业务 | 前缀/模式 | 典型 |
|------|-----------|------|
| 股息与分红 | `$BONUS_*` | `$BONUS_RATE_TTM_LAST`（股息率）≠ `$BONUS_TTM_RATE_LAST`（分红率） |
| 盈利与质量 | `$ROE_*` / `$GMR_*` / `$CORE_*` | ROE、毛利率、核心利润率 |
| 行业对比 | `$CUR_IND_*` | 分位 / 份额 |
| 估值快照 | `*_LAST` PE/PB 族 | `$PE_TTM_LAST` |
| 技术动量 | `$CHG_*` / `$BIAS_*` / `$BOLL_*` | 多日涨跌、乖离、布林（**不含「今天」**） |
| 当日涨跌 | `$PERCENT_LAST` | 今天 / 当日 / 盘中涨跌幅（实时） |

完整列名以 `action=indicators` + [fields/](fields/_index.md) 为准，勿死记本表。

---

## 7. 当日涨跌 vs 近1d（易错）

| 口语 | field | 说明 |
|------|-------|------|
| 今天涨跌 / 当日涨幅 > 1% / 盘中翻红 | `$PERCENT_LAST` | live；看 `freshness.live_quote_updated_at` |
| 日K 1 日涨跌、EOD 动量 | `$CHG_1D_LAST` | EOD 截面；label 曾写作「近1d」易误导，**不是**「今天」的默认字段 |

`index_quote_date` 滞后时两列可能分叉；问今天一律 `$PERCENT_LAST`。

---

## 8. 易错硬约束

1. **股息率 vs 分红率**：要「股息率 > 5%」用 `$BONUS_RATE_TTM_LAST`（或 LYR），**勿**用 `$BONUS_TTM_RATE_LAST`  
2. **时间窗**：要 10 年连续分红，用 `10Y` 字段，**勿**用 `3Y` 凑数  
3. **字面量**：比率 `0.05` 或 `5%`；金额 `1e8` / `1Y`；禁止对比率猜 ÷100  
4. **今天涨跌**：`$PERCENT_LAST`，**勿** `$CHG_1D_LAST`  
5. 搜不到：换词再 `indicators`；仍要内容匹配 → `search` / discover screener；仍无 → 缩池后交金融分析师 + xs-eval  
