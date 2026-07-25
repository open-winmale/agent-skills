---
name: wm-valuation
display_name: "估值解读卡"
version: 1.0.7
description: 看估值松不松、贵不贵：结合盈利能力与价格匹配给出口径清晰的判断。别和「这门生意怎么样」那张卡搞混。
---

# 估值解读卡

## 低估卡（一张多角度）

回答「贵不贵 / 是否低估」时，本卡是**一张低估判断卡**，不是按指标各发一张：

| 原则 | 说明 |
|------|------|
| **一张卡** | 对外是低估/松紧判断；PE、PB、PEG、**PR（市赚率）** 等都是**同卡内角度** |
| **情境** | 须结合**公司 · 行业 · 产业周期**综合看，禁止只扔一个倍数 |
| **人眼全页** | 需要完整市赚率看板时附 deeplink `company.undervalue`（优先 `/pr?code=`）或 page `pr` |
| **禁止** | **不新发 `wm-pr` Skill**；不平行造「市赚率低估卡 / PE 低估卡」 |

## 设计原则与要点

权威摘要见 [`references/design-principles.md`](references/design-principles.md)。一句话：

- **XS = 事实 + Gate**；**Pack = 叙事 + 透镜 + Verify**（Agent 不改数、不改 `enrich_plan`）
- **五原则**：专业、买方视角、准确、简洁、易懂（准确 > 简洁 > 填满）
- **裁决四枚举整词**：工业 公允/偏低/偏高/数据不足；金融 折价/合理/溢价/数据不足（禁复合词、禁程度副词升级）
- **诊断专名门**：`flags` 无对应旗标时禁点名"分母扩张/假便宜/席勒分叉"专名；无旗标只写分位数字 + "利润分母效应"
- **输出**：估值小表（`指标|数值|五年分位`）为主 + 行业对照表为辅；稀疏/港股缺对照零表

## 何时使用

- 「估值匹配吗 / 贵不贵 / 便宜吗 / 值不值」
- 需要盈利能力持续性 × 价格匹配的**定价备忘录**

**不要用**：问「这门生意怎么样」→ `wm-company-business`；只要一页纸 → `wm-company-card`。

Open App 无本地 LLM 时：本 Pack 的「定价备忘录终稿」不在成功标准内（可只消费 JSON，或另走 `/v1/insight/report`）。

## 多宿主（同一 HTTP）

| 宿主 | 安装 |
|------|------|
| Cursor / Claude / WorkBuddy | skills 目录下整包（**必须含 `references/`**） |
| Coze | HTTP 插件短 description + 工作流拉 references 文本 |
| Open App | `allowed_skills`；JSON 直出 |

禁止假定 NAS/本机 XS；禁止 zip 当主路径却丢掉 `references/`。

## 调用（W1）

`POST {WINMALE_API_BASE}/v1/skills/wm-valuation/run`

```json
{ "symbol": "600519", "args": { "market": "cn" } }
```

`market` 必须在 `args`。同标的会话内复用返回体（`data.*` 或兼容 `data.result.*`）。

## 强制工作流（W0–W7）

详见 `references/workflow.md`。摘要：

1. **run** → 检查 `methodology` / `enrich_plan` / `quality` / `flags`
2. `variant=blocked` → 只输出 `blocked_message`（港股金融）
3. **Read `enrich_plan.required_reads`**；禁止 `do_not_load`
4. 按 `output-skeleton`：头区散文 + 估值小表 + 对照表（辅）+ 解读；裁决四枚举整词；诊断专名门；数字照抄 JSON
5. Read `verify-checklist`；G1=0 再交付；最多回退 2 次
6. **不要**默认调用 `/v1/insight/report`（需 user JWT + 积分）

总原则：专业、买方视角、准确、简洁、易懂。不合格可检测；不承诺每次合格。字数软约束约 700～1400 汉字。

## 返回要点

**HTTP 寻址（双读）：** `data.sections` / `data.snapshot` / …；兼容 `data.result.sections`。

| 块 | HTTP（推荐） | 用途 |
|----|--------------|------|
| `freshness` | `data.freshness` | `quote_date`/`quote_sas` 对齐 `$KLINE_*_LAST`；`report_sas`=`$SAS_LAST` |
| `metrics_bar` / `sections` / `snapshot` | `data.sections` 等 | 事实（`as_of` 与 freshness 同锚） |
| `methodology` / `enrich_plan` / `quality` / `flags` | `data.methodology` 等 | 路由与按需知识；flags 含诊断旗标 |
| `is_financial` / `finance_subkind` | `data.is_financial` | Gate |

## 禁止

- 买卖点 / 猎手词（严重低估/泡沫/击球区）/ 类债终局
- 程度副词升级裁决（明显偏低/真便宜）/ 复合裁决词（公允偏低）
- 无 `flags` 对应旗标时点名诊断专名（分母扩张/假便宜/席勒分叉）
- 金融文写 EV/PEG/Schiller/DCF/FCF/净现金/净债务
- 把 JSON 表当「定价备忘录」交差
- 手写裸 eval 拼指标 / 业务参数放顶层（应进 `args`）
