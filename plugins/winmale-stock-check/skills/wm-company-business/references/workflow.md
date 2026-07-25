# 生意解读工作流（W0–W7）

不合格可检测；不承诺每宿主每次合格。总原则：专业、买方视角、准确、简洁、易懂。字数软约束（约 700～1400 汉字）。设计摘要见 `design-principles.md`。

| 阶段 | 动作 | 出口 |
|------|------|------|
| W0 Intent | 确认「生意解读」意图，非 `wm-company-card` | 意图匹配 |
| W1 Facts | `POST /v1/skills/wm-company-business/run` | 有 `methodology`/`enrich_plan`/`quality`/`snapshot` |
| W2 Route | 读 `methodology.variant`；若 `blocked` → **只**输出 `blocked_message` 结束 | 非 blocked 才继续 |
| W3 EnrichPlan | **禁止改** `enrich_plan`；记下 `required_reads` / `do_not_load` | 清单非空 |
| W4 Enrich | 按序 Read `required_reads`；禁止 Read `do_not_load` | 开写前必读完 required |
| W5 Draft | 按 `output-skeleton`：头区散文 + 对照表-only（≥2 行双侧才出表，否则零表）+ 解读；现金流类型不入表；数字照抄 JSON | 结构齐全 |
| W6 Verify | Read `verify_reads`；扫禁词与金融泄漏；最多回退重写 2 次（**静默**，勿口述） | 内部 G1=0 |
| W7 Deliver | **对用户唯一输出** = `output-skeleton` 终稿；可附 `quality.missing_fields` 一句脚注 | 读者三问可答 |

规则：默认 1× skills/run；勿扇出 follow_ups；勿默认调 `/v1/insight/report`。

## 交付合同（硬）

W0–W6 为**内部工序**，静默执行；**不得**写入读者可见回复。

**对用户可见：**

- 正常：仅 `output-skeleton` 规定的解读正文（从标题行起）
- `blocked`：仅 `blocked_message`
- 可选：文末一句缺字段脚注（来自 `quality.missing_fields`）

**禁止出现在回复中（工序元叙事）：**

- 阶段号或旁白：`W0`–`W7`、`G1=`、`G1=0`、`verify-checklist`、`enrich_plan`、`required_reads`
- 「终稿合格」「终稿已在上方交付」「快速回顾整个流程」「对照 checklist 扫描」等验收口播
- 交付后再复述一遍「三个核心结论 / 流程回顾」（skeleton 内「核心观点」三条除外）

Verify 失败 → 内部重写后再交付；仍只输出合格终稿，不解释返工过程。
