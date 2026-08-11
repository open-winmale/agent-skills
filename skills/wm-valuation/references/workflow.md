# 估值解读工作流（W0–W7）

不合格可检测；不承诺每宿主每次合格。总原则：专业、买方视角、准确、简洁、易懂。字数软约束（约 700～1400 汉字）。设计摘要见 `design-principles.md`。

| 阶段 | 动作 | 出口 |
|------|------|------|
| W0 Intent | 确认「估值匹配」意图，非 `wm-company-business`（生意解读）/ `wm-company-card`（一页纸） | 意图匹配 |
| W1 Facts | `wm-skill-run.sh wm-valuation` | 有 `methodology`/`enrich_plan`/`quality`/`flags`/`snapshot` |
| W2 Route | 读 `methodology.variant`；若 `blocked` → 输出 `blocked_message` 结束 | 非 blocked 才继续 |
| W3 EnrichPlan | **禁止改** `enrich_plan`；记下 `required_reads` / `do_not_load` | 清单非空 |
| W4 Enrich | 按序 Read `required_reads`；禁止 Read `do_not_load` | 开写前必读完 required |
| W5 Draft | 按 `output-skeleton`：头区散文 + 估值小表 + 对照表（辅）+ 解读；裁决四枚举整词；诊断专名门（flags 依据）；数字照抄 JSON | 结构齐全 |
| W6 Verify | Read `verify_reads`；扫禁词与金融泄漏；诊断专名门交叉校验；最多回退重写 2 次 | G1=0 |
| W7 Deliver | 终稿；可附 `quality.missing_fields` 脚注 | 读者三问可答 |

规则：默认 1× skills/run；勿扇出 follow_ups；勿默认调 `/v1/insight/report`。
