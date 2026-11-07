# 分析消费契约（plan_amend briefing）

给 **E1 `plan_amend`** 读，不是程序 hard 全集。一次只开本文件 + `adapt_plan.json`（或本文件对应原型节）。消费者是 deepdive S2 / Agent 深读，不是 L1 的 `wm-cashflow-quality` 等 API 卡。

程序草稿（E0）已含三表底线、COMMON 承重字段、七原型致命变量（semi）和地图校准项。Agent 只做 **升级 / 诚实 skip / 增补 / 改口 / 明确不做**，不删 A–I 底线三表。

## 铁律

- PDF 独占：分部 / 产销 / MD&A / 风险 / 历史事件；`not_found` 不补第三方。
- 准 > 全；保留原单位；只取本期列；quote+page 可 NFKC 回验。
- 诚实四态：high / low / `missing_extract` / `not_disclosed`（或 `not_applicable`）。
- 合并默认；权益 vs 并表写 `scope`。原型 F（银行/保险）NCFO 语义不同，禁止按工商业净现比硬套。
- 禁止把公司品牌名写入修订；证据只来自 `scan --summary` / `meta.priority` / `map_refs`。

## 五张分析卡（交付后按 `analysis_index.json` 消费）

**A 异常扫描**：命名字段（营收、毛利、NCFO、负债率、在建、商誉、少数股东、存货、应收），不要让分析在 100 行资产负债表里搜。

**B 营收三重拆解**：`production_sales` 全行、`segments*` 全行、合同负债、应收账款。

**C 利润除噪**：`non_recurring`、政府补助 / 公允价值 / 减值、少数股东、所得税有效税率。

**D 质地层 T5**（成对，不是孤立 quote）：致辞/`chairman_letter` vs `construction_projects`；回报表态 vs `dividend`；`risk_factors`（禁前瞻性免责）vs 减值/诉讼。

**E 七原型致命变量**：先定原型再升权。禁止给煤炭硬凑品牌护城河；禁止给银行把合同负债标 hard。

## 七原型（升权 / skip 检查单）

定原型依据：`adapt_plan.prototype`（由 `industry_hint` 映射）+ 地图信号。冲突时 `reprototype`，须附行业证据。

| 原型 | 代表业态 | 优先升权 | 默认 skip / 改口 |
|------|----------|----------|------------------|
| A 资源租金 | 煤/矿/油/部分电力 | 储量分级、产销、单位成本、长协 vs 现货、权益 vs 并表产量 | 品牌/复利叙事不强升 |
| B 周期加工 | 钢/化/建材/养殖/制造 | 产能利用率、产销、在建转固、库存 | 当期 PE 叙事不进提取 |
| C 品牌消费 | 白酒/零售/食品 | 合同负债、渠道/批价、同店、经销库存（≠公司库存） | — |
| D 技术迭代 | 半导体/创新药/智驾 | 研发费用化 vs 资本化、管线、客户集中、定点≠SOP | 规划/定点当收入 → 禁止 |
| E 平台网络 | 互联网/电信 | 用户/ARPU/出货（有表或正文才升） | 无披露则诚实 gap |
| F 资产负债表 | 银行/保险/券商/地产 | 银行 NIM/不良/资本；保险 NBV/偿付能力；地产签约/三道红线 | 合同负债/应收/存货按工商业 hard 禁止；保险 NCFO 几乎无效 |
| G 项目订单 | 机械/整车/工程 | 合同负债、在产品/存货、关联交易、在建 | 订单/框架协议 ≠ 收入 |

thin 行业（钢铁/化工/通信/互联网/农业/半导体/通用制造）：可探测、无行业 hard 清单；地图有表仍 `map_driven` 追加。不得把 `purpose_ok` 解释成「行业深研已齐」。

## 修订动作（写入 `agent_tasks_done/plan_amend.json`）

每条 `why` ≥ 8 字，并附 `evidence`（`map_ref` / `excerpt` / `filing_kind`）。

- `upgrade`：semi→hard（本份地图或原型致命变量）
- `skip`：标 `not_applicable`。**`map_refs` 含 table 禁止 skip**；三表 hard 禁止 skip
- `add`：模板外项（`id` 仅 `a-z0-9_`，须 `kind`）
- `reprototype`：改 A–G（须与 `industry_confirm` 同源或地图强信号）
- `wont_do`：只降 semi，不能覆盖 `hard`+`map_rescued`

同一 blocker 连续两次相同失败 → 换路或诚实 `not_disclosed`，禁止空转。
