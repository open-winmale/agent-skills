---
name: wm-company-business
display_name: "生意解读卡"
version: 1.1.8
description: 这门生意怎么样：赚钱模式、商业模式、靠什么赚钱、护城河与核心矛盾，用买方视角人话讲清楚。别和「贵不贵」估值卡搞混。
---

# 生意解读卡

## 设计原则与要点

权威摘要见 [`references/design-principles.md`](references/design-principles.md)；**完整能力卡设计母本**见仓库 [`docs/CAPABILITY_CARD_DESIGN.md`](../../docs/CAPABILITY_CARD_DESIGN.md)。一句话：

- **XS = 事实 + Gate**；**Pack = 叙事 + 透镜 + Verify**（Agent 不改数、不改 `enrich_plan`）
- **五原则**：专业、买方视角、准确、简洁、易懂（准确 > 简洁 > 填满）
- **三问**：生意基因 / 核心矛盾 / 定价位置（定价只定位，匹配见估值卡）
- **对照表-only**：≥2 行双侧同口径才出表，否则零表；现金流类型不入表；禁碎表与三列表

## 何时使用

- 「帮我解读这门生意 / 靠什么赚钱 / 商业模式 / 护城河 / 核心矛盾 / 业务结构」
- 需要行业透镜下的基因 / 矛盾 / 定价**事实叙事**

## 何时不要用 (When NOT to use)

- **只问「贵不贵 / 估值匹配吗」** → 使用 `wm-valuation`（估值匹配见估值卡）
- **只要 App 一页纸概况 / 查现价** → 使用 `wm-company-card`（一站式摸底）
- **查主营业务/产品收入百分比数据** → 使用 `wm-operating-segments`

Open App 无本地 LLM 时：本 Pack 的「解读终稿」不在成功标准内（可只消费 JSON，或另走 `/v1/insight/report`）。

## 多宿主（同一 HTTP）

| 宿主 | 安装 |
|------|------|
| Cursor / Claude / WorkBuddy | skills 目录下整包（**必须含 `references/`**） |
| Coze | HTTP 插件短 description + 工作流拉 references 文本 |
| Open App | `allowed_skills`；JSON 直出 |

禁止假定 NAS/本机 XS；禁止 zip 当主路径却丢掉 `references/`。

## 调用（W1）

**优先**用统一门面 `wm.sh run`（**禁止**手搓 `curl` / 自行拼鉴权 HTTP）：

```bash
bash .cursor/skills/wm-skillhub/scripts/wm.sh run wm-company-business \
  '{"market":"cn"}' --symbol 600519 --result
```

业务参数进 JSON（即 HTTP `args`）；标的优先 `--symbol`。
等价 HTTP 由脚本发出，Agent 勿直接拼鉴权。

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
| **`snapshot` / `sections` / `metrics_bar`** | **事实源**：主业、护城河相关数字、成长/负债/现金流等；Agent **必须**从这里取数 |
| `methodology` / `enrich_plan` / `quality` / `flags` | 路由与按需知识（读 `enrich_plan.required_reads`） |
| `is_financial` / `finance_subkind` | Gate |
| **`render`** | **仅骨架占位**（`markdown_skeleton` / `preferred`），**不是**终稿正文；禁止把 `render` 当「已写好的生意解读」 |

**契约：** XS 出可对账事实（`snapshot`…）；叙事正文由 Agent 按 Pack `references/` + `enrich_plan` 写。Open App 无本地 LLM 时可只消费 JSON。

## 禁止

- 把 JSON 表当「解读」交差
- **把 `render` / `markdown_skeleton` 当终稿正文**（须读 `snapshot` 再按 enrich_plan 写）
- 业务参数放顶层（应进 `args`）
- 手写裸 eval 拼指标
- 金融文写净现比/八型
- **工序元叙事**：向用户口述 W0–W7 / G1 / verify / 流程回顾 / 终稿合格
