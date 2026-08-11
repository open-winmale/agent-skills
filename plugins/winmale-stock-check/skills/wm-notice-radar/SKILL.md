---
name: wm-notice-radar
display_name: "公告搜索"
version: 1.2.0
description: 查询 A 股/港股公司公告，或按类别/减持回购信号扫描。用户问公告、业绩预告、减持回购、全市场公告汇总时使用。仅交易所公告，不含财经媒体/舆情新闻。美股暂不支持（返回 UNSUPPORTED_MARKET）。
---

# 公告搜索

## 何时使用

- 「最近有什么公告」「有没有业绩预告」
- 「是否出现减持/回购信号」
- 「最近 N 天全市场公告汇总 / 哪些值得关注」（**未点名单票**）

## 市场范围

| 市场 | 单票 list/signal | 全市场 digest/category |
|------|------------------|------------------------|
| **A 股 (cn)** | ✅ 自动（6 位代码） | ✅ 默认；或 `market=cn` |
| **港股 (hk)** | ✅ 自动（1–5 位如 `00700`） | ✅ `market=hk` |
| **美股 (us)** | ❌ `UNSUPPORTED_MARKET` | ❌ 暂无公告库 |

港股类别正则已含繁体（如 `購回`/`業績`）。**不要**把港股空列表当成「没公告」而不看 `error`/`market`。

## 何时不要用 (When NOT to use)

- **查询定期报告 (年报/半年报/季报) PDF 与列表** → 使用 `wm-filings`（财报检索）
- **仅查自选关注列表里的相关动态** → 使用 `wm-watchlist`（关注列表）
- **查三表多期财务数据** → 使用 `wm-statements`（财务报表 3+1）
- **财经媒体 / 舆情 / 网页新闻** → **本技能不做**（仅交易所公告）；系统无新闻 vfunc，勿外搜充当证据
- **美股 SEC/交易所公告** → 暂不支持；勿假装有结果

## 库主人

- 域库：`sys/notice.*`（本技能最熟练；无独立 host selector）
- 速查：[references/lib.md](references/lib.md)
- 技能 mode：`list` / `category` / `signal` / `digest`；更细查询用 notice.query_* / store_find

### digest vs list（易空）

| mode | 语义 | 空结果常见原因 |
|------|------|----------------|
| `list` + `symbol` | 该股**全部类型**公告 | 窗口内确实无公告；或美股不支持 |
| `digest` | 全市场仅 **forecast + reduction + buyback** 三类聚合 | 窗口内这三类没有命中 → `by_category` 可全空；**不等于** list 坏了 |
| `category` | 单类别全市场 | 类别正则无命中 |

空 digest 时：说明三类雷达无信号，或改 `window`；不要据此推断「公告接口挂了」。

## 超出 action

```text
1) 先 list / category / signal / digest
2) 自由标题、多票、未登记类别、某日全量 → 带已用 window/category 上下文交 wm-xs，复用 notice.*
3) 禁止外搜新闻；禁止把全市场做成「我的关注」汇总
```

## 范围选择（极易错）

| 用户说法 | 正确做法 | 禁止 |
|----------|----------|------|
| 某公司最近公告 | `mode: list` + `symbol` | — |
| **全市场 / 最近几天公告报告 / 值得关注的公告**（未说「我的关注」） | **`mode: digest`**（一次 forecast+reduction+buyback）；或连打三次 `category` | **禁止**只扫 `forecast`；**禁止**用无标的的 `signal`；**禁止**默认先拉 `wm-watchlist` |
| 港股全市场大事 | `digest` + `market=hk` | 勿用默认 cn 扫港股 |
| 单票有没有减持/回购 | `mode: signal` + `symbol` | 勿当全市场雷达 |
| 「我的关注 / 自选里有什么大事」 | 关注列表 Role + watchlist，再按成分查公告 | 勿说成「全市场」 |

WorkBuddy 真实踩坑：用户要「最近7天公告报告、中翻中」，Agent 却汇总了关注列表——**范围错误，一票否决。**  
另一踩坑：全市场报告误走 `signal` 后自称「扫不到减持」——应走 **`digest` / `category`**，不是接口缺能力。

## 调用

**优先**用统一门面 `wm.sh run`（**禁止**手搓 `curl` / 自行拼鉴权 HTTP）：

```bash
bash .cursor/skills/wm-skillhub/scripts/wm.sh run wm-notice-radar \
  '{"mode":"list","window":"1m","limit":20}' --symbol 600519 --result
```

港股单票：

```bash
bash .cursor/skills/wm-skillhub/scripts/wm.sh run wm-notice-radar \
  '{"mode":"list","window":"1m","limit":20}' --symbol 00700 --result
```

业务参数进 JSON（即 HTTP `args`）；标的优先 `--symbol`。
等价 HTTP 由脚本发出，Agent 勿直接拼鉴权。

**`mode` / `window` / `limit` / `category` / `signal` / `market` 一律进包装脚本的 JSON 参数（即 HTTP `args`）。**

### 全市场「值得关注」（默认连打三类别）

**优先一次 `digest`**（服务端并行查 forecast + reduction + buyback）：

```bash
bash .cursor/skills/wm-skillhub/scripts/wm.sh run wm-notice-radar \
  '{"mode":"digest","window":"7d","limit":50}' --result
```

港股全市场：

```bash
bash .cursor/skills/wm-skillhub/scripts/wm.sh run wm-notice-radar \
  '{"mode":"digest","window":"7d","limit":50,"market":"hk"}' --result
```

等价：`mode=category` + `category=watch`（或 `worth`）。  
若必须分次调用，则**连续三次** `category`（缺一不可）。

写报告时合并三类结果，用白话中文突出主题与个股线索，**勿编造未返回的财务数字**。**禁止**只扫业绩预告就声称「全市场大事报告」。

### 单票公告列表（默认 list）

```bash
bash .cursor/skills/wm-skillhub/scripts/wm.sh run wm-notice-radar \
  '{"mode":"list","window":"1m","limit":20}' --symbol 600519 --result
```
