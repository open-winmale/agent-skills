# 策略迭代：胜率 · 归因 · 再跑

核心理解：**历史拨测 = 用过去数据验证逻辑与参数，做成败归因，小步迭代。**  
复盘最专业的数据源是 **执行历史（ledger/holdings/equity）+ 执行过程日志（trace/factors/events）**，不是只看总收益。  
不是代客下单；结论不构成投资建议。核对表见 [review.md](review.md)。

## 1. 目标与闭环

```text
基线 → 假设（只改一类）→ lint → preview → run
  → 拉执行历史 + 过程日志（§2）
  → 成败归因（§4）→ 1～3 条改法 → 再跑
```

参数用 `simulation.tuning`；逻辑改动走 `project_write`+publish 或新 `run_custom`。

---

## 2. 工具：打日志 + 拉一次执行的日志

### 2.1 跑的时候怎么打日志（写进阶段 XS）

须先 `xs.require("xs/simulation/lib/init.xs")`（或至少 `trace.xs`）。  
写入 `bt.trace`，引擎日终 drain → 持久化为 **trace_summary / factor_rows**。

| API | 阶段 | 用途 |
|-----|------|------|
| `simulation.trace(step, code, message, detail)` | 任意 | 通用结构化日志；**仅 4 参** |
| `simulation.check(sym, id, label, value, thr, pass)` | selector | 单项检查（不自动否决） |
| `simulation.reject(sym, message, checks)` | selector | 否决原因（`XS_FILTER_REJECT`） |
| `simulation.factor(sym, factors_map)` | trading | 因子暴露 |
| `simulation.summary(step, message, detail)` | 任意 | 阶段汇总 |
| `simulation.risk_reject` / `risk_clip` | risk | 风控否决/裁剪可观测 |

```xs
xs.require("xs/simulation/lib/init.xs")
# trading 示例：入场决策打点
simulation.trace("trading", "XS_TRACE", "pe_entry", {
  "sym": sym, "pe": pe, "w": w
})
simulation.factor(sym, {"pe": pe, "w": w})
```

`step` 建议：`selector` | `selector_rank` | `trading` | `risk` | `group_label`。  
`code` 常见：`XS_TRACE` / `XS_FILTER_REJECT` / `XS_TRACE_SUMMARY` / `RISK_REJECT` / `RISK_CLIP`。  
详 API：[simulation-api.md](simulation-api.md)。

**原则**：归因依赖日志——关键分支（入选/剔除、下单/跳过、裁剪）必须有一条 trace；勿只 `return` 无打点。

### 2.2 跑完怎么拉「一次执行」的数据（管理面）

结果面可能很大：**禁止默认全量**。按档拉取，用 `page_limit` / `page_cursor`（勿传引擎保留名 `cursor`）。

| 档 | 体积 | 拿什么 |
|----|------|--------|
| L0 | 小 | `_backtest_summary`；`_backtest_trace` 默认 `page_view=summary`（`by_code` / `top_codes`） |
| L1 | 中（分页） | `_backtest_deep` 默认 `audit`（equity/ledger/holdings 各一页）；trace `page_view=factors` |
| L2 | 叙事流 | host `backtest.events`（`after_seq`+`limit`；需 `event:read`；7d TTL） |

优先 **platform_free**（免 EC；需 `analysis:backtest:read`）：

| 顺序 | script_ref | 拿到什么 |
|------|------------|----------|
| 1 | `_backtest_summary.xs` | metrics |
| 2 | `_backtest_deep.xs` | 执行历史（分页） |
| 3 | `_backtest_trace.xs` | 过程摘要 → 再 factors 页 |

```json
{"mode":"call","script_ref":"xs/ops/_backtest_deep.xs","args":{"run_id":"<id>","page_view":"audit","page_limit":50},"symbol":"600519","market":"cn"}
{"mode":"call","script_ref":"xs/ops/_backtest_deep.xs","args":{"run_id":"<id>","page_view":"field","page_field":"ledger","page_limit":50,"page_cursor":"<next>"},"symbol":"600519","market":"cn"}
{"mode":"call","script_ref":"xs/ops/_backtest_trace.xs","args":{"run_id":"<id>","page_view":"summary"},"symbol":"600519","market":"cn"}
{"mode":"call","script_ref":"xs/ops/_backtest_trace.xs","args":{"run_id":"<id>","page_view":"factors","page_limit":50},"symbol":"600519","market":"cn"}
```

| free 参数 | 含义 |
|-----------|------|
| `page_view` | deep: `meta`\|`audit`\|`field`；trace: `summary`\|`factors`\|`all` |
| `page_limit` | 默认 50，最大 200（host 单页上限 500） |
| `page_cursor` | 上一页返回的 `next_cursor` |
| `page_field` | deep+`field`：`equity`\|`ledger`\|`holdings` |

等价 host（分页选项；大数组**不在** `run_get` 里）：

```xs
rid := "<run_id>"
opts := {"limit": 50, "cursor": ""}
return {
  "ledger": backtest.run_ledger(rid, opts),
  "equity": backtest.run_equity(rid, opts),
  "holdings": backtest.run_holdings(rid, opts),
  "trace": backtest.run_trace_summary(rid),
  "factors": backtest.run_factors(rid, opts),
}
```

**叙事日志 / 相位**（需 `analysis:backtest:event:read`）：

```xs
backtest.events(rid, {"after_seq": 0, "limit": 50, "type": "log", "step": "risk", "level": "warn"})
# 续拉：after_seq = 上一页返回的 next_seq
```

| options | 说明 |
|---------|------|
| `after_seq` / `limit` | seq 分页；回 `has_more` / `next_seq` |
| `type` | `log`\|`phase`\|`progress`\|`nav`\|`done`\|`error` |
| `step` | log：`system`\|`warmup`\|`selector`\|`trading`\|`risk`\|`match`\|`corporate`\|`portfolio`\|`group_label` |
| `level` | log：`info`\|`warn`\|`error`\|`debug` |
| `code` | log：稳定码如 `RISK_REJECT`（大小写不敏感，入库为大写） |

带 `step`/`level`/`code` 且未写 `type` 时，host **强制 `type=log`**（服务端 Mongo 过滤 `payload.*`）。REST：`GET .../runs/{id}/event-log?step=&level=&code=&after=&limit=`。归因主路径仍可优先 **ledger + trace_summary/factors**。

### 2.3 数据源怎么分工（专业复盘）

| 问题 | 优先看 |
|------|--------|
| 有没有按规则成交？仓位对不对？ | **ledger** + holdings（deep） |
| 净值怎么走？哪天拐？ | **equity** |
| 选股为何踢掉 / 交易为何跳过 / 风控裁了谁？ | **trace**（reject / clip / 自定义 message） |
| 因子暴露是否按设计？ | **factors** |
| 跑批卡住/暂停？ | status + **events** |

没有 trace 打点 → 只能猜「规则是否触发」；自定义单元务必在关键路径打点后再复盘。

示例入口：`examples/deep_results_eval.json`（deep）；拉完再调 `_backtest_trace.xs`。

---

## 3. 成败归因检查表

### 成功时

| 问 | 看 |
|----|-----|
| 赚在哪几只 / 哪段？ | holdings + equity + ledger |
| 选股是否真过滤？ | holdings ∩ filter；trace `XS_FILTER_REJECT` |
| 仓位是否符合 weight？ | ledger BUY；对照 trace 里的 `w` |
| 单票偶然？ | 换宇宙再跑 |

### 失败时

| 问 | 看 |
|----|-----|
| 规则没触发？ | trading 早退；trace 无 pe_entry；等权躺平 |
| weight 写成现金？ | ledger 仓位远超设定 |
| 风控裁剪？ | trace `RISK_CLIP` / `RISK_REJECT`；`risk.max_*` |
| 池空 / bar_ok 全假？ | trace；未 init |
| 参数未生效？ | tuning vs 未声明 script_params |

---

## 4. 找因子 / 改逻辑（最小步）

1. 固定宇宙窗口，基线 + **带打点**的自定义版各跑一趟。  
2. 只改 selector **或** trading **或** 一个 tuning。  
3. 用 §2 拉 deep+trace，对照 metrics / 持仓 / 日志码。  
4. 有效则固化；无效记排除项。  

过拟合：宇宙过小、窗口过短、调参过多 → 样本外或换宇宙；勿把单次最优说成「必赚」。

---

## 5. 对人输出合同

1. **历史验证**（指标 + 机制）  
2. **执行证据**：至少引用 ledger 或 trace 中 1～2 条（日期/代码/动作）  
3. **成败归因**  
4. **1～3 条可再跑改法**（含「补打点」若日志不足）  
5. **边界**：不构成投资建议；非代客下单  
