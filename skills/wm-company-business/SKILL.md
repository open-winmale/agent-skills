---
name: wm-company-business
display_name: "生意解读卡"
version: 1.1.4
description: 这门生意怎么样：赚钱模式、护城河与隐患，用人话讲清楚。别和「贵不贵」估值卡搞混。
---

# 生意解读卡

## 设计原则与要点

权威摘要见 [`references/design-principles.md`](references/design-principles.md)；**完整能力卡设计母本**见仓库 [`docs/CAPABILITY_CARD_DESIGN.md`](../../docs/CAPABILITY_CARD_DESIGN.md)。一句话：

- **XS = 事实 + Gate**；**Pack = 叙事 + 透镜 + Verify**（Agent 不改数、不改 `enrich_plan`）
- **五原则**：专业、买方视角、准确、简洁、易懂（准确 > 简洁 > 填满）
- **三问**：生意基因 / 核心矛盾 / 定价位置（定价只定位，匹配见估值卡）
- **对照表-only**：≥2 行双侧同口径才出表，否则零表；现金流类型不入表；禁碎表与三列表

## 何时使用

- 「帮我解读这门生意」「公司速览 / 三层穿透」
- 需要行业透镜下的基因 / 矛盾 / 定价**事实叙事**

**不要用**：只要 App 一页纸 → `wm-company-card`。

Open App 无本地 LLM 时：本 Pack 的「解读终稿」不在成功标准内（可只消费 JSON，或另走 `/v1/insight/report`）。

## 多宿主（同一 HTTP）

| 宿主 | 安装 |
|------|------|
| Cursor / Claude / WorkBuddy | skills 目录下整包（**必须含 `references/`**） |
| Coze | HTTP 插件短 description + 工作流拉 references 文本 |
| Open App | `allowed_skills`；JSON 直出 |

禁止假定 NAS/本机 XS；禁止 zip 当主路径却丢掉 `references/`。

## 调用（W1）

`POST {WINMALE_API_BASE}/v1/skills/wm-company-business/run`

```json
{ "symbol": "600519", "args": { "market": "cn" } }
```

`market` 必须在 `args`。同标的会话内复用 `data.result`。

## 强制工作流（W0–W7）

详见 `references/workflow.md`。摘要（**内部静默执行**；用户只见 W7 终稿）：

1. **run** → 检查 `methodology` / `enrich_plan` / `quality`
2. `variant=blocked` → 只输出 `blocked_message`（港股金融）
3. **Read `enrich_plan.required_reads`**（含 workflow + instruction + lens…）；禁止 `do_not_load`
4. 按 `output-skeleton`：头区散文 + **对照表-only**（本章 ≥2 行双侧同口径才出表，否则零表）+ 解读散文；无「本公司指标」表；现金流类型不入表；表内数字准确照抄 JSON；无 `top_share` 不写精确占比；解读走透镜、禁行业套话串味
5. Read `verify-checklist`；内部 G1=0 再交付；最多回退 2 次（勿口述验证过程）
6. **不要**默认调用 `/v1/insight/report`（需 user JWT + 积分）

**交付：** 对用户**唯一**输出 `output-skeleton` 正文（blocked 时仅 `blocked_message`）。禁止 W 阶段旁白、`G1=`、流程回顾、终稿合格口播。

总原则：专业、买方视角、准确、简洁、易懂。不合格可检测；不承诺每次合格。字数软约束约 700～1400 汉字。

## 返回要点

| 块 | 用途 |
|----|------|
| `metrics_bar` / `sections` / `snapshot` | 事实 |
| `methodology` / `enrich_plan` / `quality` / `flags` | 路由与按需知识 |
| `is_financial` / `finance_subkind` | Gate |

## 禁止

- 把 JSON 表当「解读」交差
- 业务参数放顶层（应进 `args`）
- 手写裸 eval 拼指标
- 金融文写净现比/八型
- **工序元叙事**：向用户口述 W0–W7 / G1 / verify / 流程回顾 / 终稿合格
