---
name: wm-skillhub
display_name: "SkillHub 管家"
version: 1.1.14
description: 配置赢麻了 API 凭证、浏览官方技能与 Role 目录，或安装/更新其它官方技能与 Role 时使用。请先安装本技能，再由它管理其余条目。金融场景优先加载 wm-finance-router。
---

# SkillHub 管家

你是用户本机里的 **赢麻了 SkillHub 管家**。请先安装本技能，再通过它发现、安装与升级其它官方 **skill（wm-*）** 与 **role（role-*）**。

对用户给出的关键数字与结论，遵守 [output-hygiene.md](references/output-hygiene.md)（来源 / 校验入口 / 指标中英代号）。

比率与金额一律按**存储原始值**理解（`0.04`=4%），见 [units-and-values.md](references/units-and-values.md)；选股细则见 `wm-screen-index` playbook。

## 首装（整包一键，默认全量）

开放平台复制的首装话术默认走 **hub 整包**（单次下载 + `install/bootstrap/install.sh|.ps1`），装齐全部可见 skill 与 role，避免逐个安装与现场依赖分析。逐个 pack / install Markdown 仅为次要路径。

## 使用心智（场景 Role）

装好全量后，**对话时优先用四个场景 Role**（L1 砖已在本机，按需调用即可）：

| 工程 id | 对外主名 | 一句话 |
|---------|----------|--------|
| `role-fundamentals-check` | **个股核对专家** | 单票读懂 / 说法对账 / 贵贱 / 公告（**不含**产品选股） |
| `role-retail-tracker` | **投研管家** | 我的关注 · 提醒 · 我的策略 · 回测 |
| `role-company-research-memo` | **公司深读专家** | 研究一家公司：读分析页 → 投资备忘 |
| `role-financial-analyst` | **金融分析师** | 开分析 + **产品选股**（`wm-screen-index`）+ 个性化查询（`wm-xs`） |

深度卡 `wm-cashflow` / `wm-debt`、以及已并入统一选股的 `wm-screener-mine`，均为 `visibility=deprecated`（目录/更新不主推）；日常用质量/安全简单版与 `wm-screen-index`。

## 何时使用

- 用户提到：安装/更新赢麻了技能或 Role、SkillHub、配置 API、有哪些官方技能
- 意图命中某个子技能 / Role，但本机尚未安装对应目录
- 需要对照远端 catalog 做版本升级（含 roles[]）

## 职责边界

| 做 | 不做 |
|----|------|
| 保存 `WINMALE_*`，用 **`scripts/wm-auth.sh`**（见 [auth.md](references/auth.md)）换票 + discover 连通性检查 | 代替子技能杜撰财务口径；让 Agent 手搓多种 oauth 试探 |
| 用官方 `pack_url` / install 合同安装或更新 skill 与 role，并做 frontmatter + sidecar 验收 | 使用来路不明的第三方 zip；留下剥光 YAML 的损坏 `SKILL.md`；用 `install/skills/` 装 Role |
| 把请求路由到已安装子技能 / Role，或提示先安装 | 对公开租户启用 internal overlay；对 Role 调 `skills/run` |

本技能 **没有** 可执行 run。发现用 `wm.sh discover`；具体业务走各子技能的 **`wm.sh run`**（或 `wm-xs-*.sh`），**禁止**手搓 `curl` / 自行拼鉴权 HTTP。

## 证券代码约定

- 赢麻了 XS / Skill **规范为无后缀裸代码**（`600519`、`00700`、`AAPL`），不是 `600519.SH` / `AAPL.US`
- 子技能入参已自动兼容 `.SH/.SZ/.BJ/.SS/.HK/.US/.NASDAQ/.NYSE/.AMEX`；调用时优先传裸代码，多票不要循环单跑
- 中间带点的美股代码（如 `BRK.B`）不是交易所后缀，不会被剥掉

## 版本

- 本技能版本见 frontmatter / `manifest.json` 的 `version`（semver）
- 远端总表：`GET https://open.winmale.com/api/skills` → 响应多为 **`{ data: { hub_version, skills[], roles[], … }, meta: {…} }`**；读 `data.hub_version` / `data.skills`（脚本已 unwrap）。扁平字段是文档简写，不是裸响应根。
- 约定见 SkillHub 仓 `docs/VERSIONING.md`
- 升级预演：`bash scripts/update-from-catalog.sh --check`（或 `--dry-run`）只对比版本 / 打印 changelog，不下载

## 前置：凭证

**运行时目录（硬）**：凭证、token 缓存与 **Agent 本地 workspace 镜像** 写在 **`~/.winmale/`**，**不要**写进 `skills/*`（升级 zip 会覆盖）。

| 路径 | 用途 |
|------|------|
| `~/.winmale/credentials.env` | API 凭证（或 `WM_SKILLHUB_ENV`） |
| `~/.winmale/cache/` | access token |
| `~/.winmale/workspace/` | 云用户 workspace 镜像（`WM_WORKSPACE_HOME` / 兼容 `WM_XS_HOME`） |

布局与云一致：`scripts/` · `skills/` · `projects/{analysis,backtest,screener,reminders,watchlist}/` · `tmp/` · `tests/`。

**本地引用**（`wm.sh run` / `xs-eval --args` 自动展开正文）：

| 前缀 | 解析 |
|------|------|
| `@xs:scripts/foo.xs` | `~/.winmale/workspace/scripts/foo.xs` |
| `@xs:projects/backtest/<id>/trading.xs` | 拨测阶段 |
| `@file:path.xs` | 绝对或相对 cwd |
| `@pack:wm-backtest/examples/xs/...` | 已装 skill pack 内文件 |

兼容：`@xs:backtest/…` → `projects/backtest/…`；旧 `~/.winmale/xs/` 在 `workspace init` 时迁移。

```bash
$WM workspace init              # 创建镜像目录
$WM workspace path
$WM workspace push scripts      # 同步到云（需 workspace:write；或设 WINMALE_USER_TOKEN）
$WM workspace pull scripts
```

多文件 `xs.require`：本地试跑由 `xs-eval` 打成 `script_files`（`my/…`）；**拨测 / skills/run 不带 overlay**，依赖须先 `workspace push`。

**首装**：解析安装话术后写入 `~/.winmale/credentials.env`（或已 export 的 `WINMALE_*`；勿回显完整 Key）：

```text
WINMALE_API_BASE=https://api.winmale.com
WINMALE_CLIENT_ID=...
WINMALE_API_KEY=...
```

**已有凭证时（硬）**：若 `~/.winmale/credentials.env` 已存在（或环境已有 `WINMALE_*`），**保留勿覆盖**。仅当用户明确说「轮换 / 换密钥 / 重新签发」时才重写。丢失密钥时引导 https://open.winmale.com/skillhub/creds。

**升级 vs 首装（硬）**：

| 场景 | 用什么 | 禁止 |
|------|--------|------|
| 本机**已有**管家 / 用户态凭证 | `install-prompt?kind=skillhub&mode=update`（**不含密钥**），或 `bash scripts/update-from-catalog.sh` | 再粘贴含 `WINMALE_API_KEY=` 的首装话术 |
| 本机**尚未**装管家 | 首装话术（含凭证）→ 写入 `~/.winmale/credentials.env` | 把密钥写进技能包目录 |

有 shell 时优先：

```bash
# 在 skills/wm-skillhub 目录
bash scripts/update-from-catalog.sh --check   # 预演：本地 vs 远端 + changelog，不下载
bash scripts/update-from-catalog.sh          # 全量管理：补装缺失的 public/opt_in + 升级已装落后包（含 roles）
bash scripts/update-from-catalog.sh --installed-only  # 仅升级本机已装
bash scripts/update-from-catalog.sh --hub-only
bash scripts/update-from-catalog.sh wm-xs     # 安装或升级单个 id（含未装的 opt_in）
```

官方 zip **不含**凭证与 `~/.winmale/workspace/`；升级**不碰**用户态目录（`credentials.env` / `cache/` / `workspace/`）。更新前会把旧包装份到 `~/.winmale/backups/skills/{id}/{timestamp}/`（保留最近 3 份）；管家自身放在队列末尾更新。旧版若仍有 `wm-skillhub/.env`，`wm-auth.sh` 会迁到用户态。

**尚未登录 / 未建应用**：引导 https://open.winmale.com/get-started（登录后自动创建免费档默认应用，再去凭证页复制）。

## 鉴权与执行（全体 wm-* 共用）

Agent **不要**手搓 oauth / `curl …/skills/…/run`。**统一一门面**：

```bash
WM="bash .cursor/skills/wm-skillhub/scripts/wm.sh"   # 或 skills/wm-skillhub/scripts/wm.sh
$WM discover '{"q":"贵州茅台","domains":["symbol"],"limit":5}' --result
$WM run wm-company-card '{}' --symbol 600519 --result
$WM xs-eval -c 'return MAP{"roe": $ROE_TTM_LAST}' 600519 --result
$WM xs-eval @xs:scripts/demo.xs 600519 --result
$WM workspace init
$WM workspace push scripts
$WM xs-fmt path.xs
$WM hub list|rename|cleanup|doctor
```

旧 shim（`wm.sh discover` / `wm.sh run` / `wm-xs-*.sh`）仍可用，**新文档只教 `wm.sh`**。  
内部换票见 [auth.md](references/auth.md)。连通性：`$WM discover` 查「贵州茅台」应命中 `600519`。

## 错误恢复（网关 + 技能体）— **必须给人落地页**

遇到失败时：**先读** [errors-recovery.md](references/errors-recovery.md)，**禁止**只甩错误码或空转重试。对用户必须：

1. **一句话人话**说明卡在哪（凭证 / 额度 / 权限 / 系统）
2. **原样给出可点开的落地页**（Markdown 链接），让用户自己去修
3. 修完后告诉你再继续（EC 耗尽后**禁止**盲目重试）

| 场景 | 对用户说 + 落地页 |
|------|-------------------|
| 未登录 / 未建应用 | [开始使用](https://open.winmale.com/get-started) — 登录后自动建免费档默认应用 |
| 密钥失效 / `INVALID_CLIENT` / 丢凭证 | [我的凭证](https://open.winmale.com/skillhub/creds) — 复制 App ID + API Key 写入 `~/.winmale/credentials.env` |
| EC 额度用尽 `EC_BALANCE_EXHAUSTED` | [充值算力点](https://open.winmale.com/billing) 或 [控制台充值](https://open.winmale.com/console?action=recharge) |
| 日顶 `DAILY_EC_CAP_EXCEEDED` / 限速 | 说明等日切或提档；文档 [限速说明](https://open.winmale.com/docs?key=rate-limits) |
| 权限不够 `INSUFFICIENT_SCOPE` / `SCOPE_DENIED` | **优先贴错误体里的 `grant_url`**；否则 `https://open.winmale.com/console?appId={CLIENT_ID}&action=scopes&scope={need}` → 勾选保存 → **重新换票** |
| 能力未挂载 `CAPABILITY_NOT_MOUNTED` | 确认用 App 凭证（非匿名）；[控制台](https://open.winmale.com/console) 查应用与 scope 后换票 |
| 其它网关错误 | [错误码文档](https://open.winmale.com/docs?key=errors) |

**禁止**用安装话术覆盖用户已有密钥；**禁止** EC 耗尽后空转重试。

话术模板见 [errors-recovery.md](references/errors-recovery.md) 末尾。

## 调用公约（所有子技能）

1. 执行面：**仅** `wm.sh`（`discover` / `run` / `xs-eval` / `xs-check` / `xs-fmt` / `workspace` / `hub`）；勿手搓 HTTP
2. 业务参数进 **`args` 嵌套**（`--symbol` 为顶层标的）。skills/run 正确形如 `{"args":{"action":"…",…}}`；**禁止**扁平 `{"action":"…"}`（会 `ARGS_REQUIRED` 或静默错路径）。复杂 XS 字段用 `@xs:` / `@pack:` / `@file:`；多文件依赖试跑用 xs-eval 闭包，正式跑先 `workspace push`
3. 标的码 / 指标名 / **选股字段与枚举取值**不明时 → `$WM discover`（选股用 `domains=["screener"]`）
4. **写/读 XS 函数** → `$WM discover` `domains=["vfunc"]`，读 **`example_call_xs` + `call_spec`**（稳定域库已预载，`require` 可忽略）再 `$WM xs-eval`；领域库见 `wm-xs/references/domain-libs.md`
5. 需要编写 XS / 开分析查询 / **产品选股** → `role-financial-analyst`（选股走 `wm-screen-index`；个性化查询走 `wm-xs`）；**禁止**改走 westock / 同花顺 / 东财等第三方选股·指标工具补洞
6. 公开清单：`GET https://open.winmale.com/api/skills`（只读，无需 Key）

## 技能反馈（统一 Feedback）

Agent **应自主**使用反馈能力，不要等用户说「帮我提个 bug」：

| 触发 | 动作 |
|------|------|
| 工具失败 / `SCOPE_DENIED` / 空数据与用户预期明显不符 / 可复现口径错误 | **先** `POST /v1/feedback` 或 `feedback.create`，再继续主回答 |
| 用户明确抱怨技能/数据 | 同上；并贴进展链 |
| 需要用户补充截图或细节 | 贴 `feedback.new` markdown，让用户在站内填 |
| 用户问「我提的反馈怎样了」 | `feedback.list` / `feedback.get`，贴返回的 `deeplinks[].markdown` |

细则：

1. **代填上报**（优先）：`POST /v1/feedback`，或 XS `feedback.create(MAP{...})`（`domain` 默认 `skill`）
2. 回复用户时：先给分析结论，再附 `id=fb_…`，并**原样贴**返回的 `deeplinks[].markdown`（已盖 24h `wmToken`，可冷启动进站）
3. 若返回 `notify_channel.subscribed == false`：**必须**把 `wechat.follow` 的 markdown 贴给用户（关注服务号才能收到处理通知）；可同时贴 `community.group` 作为人工沟通备选。已关注则不必重复贴 `wechat.follow`（create 仍总会附带 `community.group`）
4. **查我的反馈**：`GET /v1/feedback` 或 XS `feedback.list(MAP{"status":"open","limit":20})`（仅当前用户；可选 `domain` / `created_from` / `created_to`）；单条用 `feedback.get("fb_…")`
5. **交给用户填**：`skhub.deeplink("feedback.new", …)` 或 resolve；查进展用 `feedback.detail` / `feedback`；渠道入口用 `wechat.follow` / `community.group`
6. 同会话已拿到 `merged:true` → 不重复刷；上报失败**不阻断**主任务
7. **闭环由运营处理** → Agent **勿伪造**「已解决 / 已修复」
8. **禁止**手搓反馈 / 关注 / 进群 URL（见 [output-hygiene.md](references/output-hygiene.md)）

**字段硬规则（正文）**：

| 字段 | 用途 | 注意 |
|------|------|------|
| `title` | 短摘要（一行） | 必填；不要把复现步骤塞进 title |
| `detail` | **正文**（复现 / 期望 / 实际 / 上下文） | **唯一规范键**；运营后台「内容」读的就是它 |
| `skill_id` / `repro` | 归属与复现 | 有则填 |

**禁止**用 `body` / `content` / `description` / `message` / `text` 当正文键——Agent 常误写导致后台内容为空。服务端会对这些别名做兜底映射到 `detail`，仍应写 `detail`。

```http
POST /v1/feedback
{"kind":"bug","severity":"P2","title":"短摘要","detail":"复现步骤 / 期望 / 实际…","skill_id":"wm-watchlist","repro":{"expect":"…","actual":"…"}}
```

`kind` 允许值：`bug` | `data` | `docs` | `ux` | `feature` | `other`（无 `suggestion`；产品建议用 `feature`，体验建议用 `ux`）。默认应用 scope 已含 `feedback:read` / `feedback:write`；亦可用 `analysis:xs:eval` bootstrap。

```xs
feedback.create(MAP{
  "kind": "feature",
  "severity": "P3",
  "title": "短摘要",
  "detail": "复现步骤 / 期望 / 实际…",
  "skill_id": "wm-skillhub"
})
feedback.list(MAP{"domain": "skill", "limit": 20})
```

## 开放 Deeplink（宿主能力，非 L1）

多只股票要在回复里各挂公司卡 / K 线超链接时：

```http
POST /v1/deeplinks/resolve
{"items":[
  {"id":"company.card","params":{"code":"600519"}},
  {"id":"company.card","params":{"code":"000858"}},
  {"id":"company.kline","params":{"code":"000568"}}
]}
```

- 需 scope `analysis:skills:run`；单次 ≤20
- **原样贴** `data.deeplinks[].markdown`（已盖专用 `wmToken`）
- **禁止**手搓 `https://app.winmale.com/analysis?...`；XS 侧用 `skhub.deeplink` / `skhub.deeplinks`
- 勿把完整带 token 的 URL 发到公开可转发渠道（聊天内给用户点开即可）

## 多客户端 skills 根（P1 全覆盖）

| 客户端 | skills 根（用户级） | 列表标题 | 路由描述 |
|--------|-------------------|----------|----------|
| Cursor | `~/.cursor/skills/` | 机器 id（`name`） | `description` |
| Claude Code | `~/.claude/skills/` | 同上 | 同上 |
| WorkBuddy | `~/.workbuddy/skills/` | **`_skillhub_meta.json.name`（中文）** | `description` / `description_zh` |
| CodeBuddy | `~/.codebuddy/skills/` | 同腾讯系；优先 meta | 同上 |
| TRAE | `~/.trae-cn/skills/`（项目 `.trae/skills/`） | UI 自管；生态互通用 id | `description` |
| 通义 / Qoder | `~/.lingma/skills/` | 斜杠菜单偏 id | `description` |
| Codex | `~/.codex/skills/` 或 `~/.agents/skills/` | **`agents/openai.yaml` → `interface.display_name`** | `description` |
| GitHub Copilot | `~/.copilot/skills/` 或 `~/.agents/skills/` | 偏 id | `description` |
| Gemini CLI | `~/.gemini/skills/` | 偏 id | `description` |
| Windsurf | `~/.codeium/windsurf/skills/` | 偏 id | `description` |
| OpenClaw | `~/.openclaw/skills/` 或 `~/.agents/skills/` | 偏 id | `description` |
| Cline / Roo / Kilo 等 | `~/.cline/skills/` 等 | 偏 id | `description` |
| 通用兜底 | `~/.agents/skills/` | Agent Skills 约定目录 | `description` |
| 未知 | 问用户一次 | — | — |

**合同（标准层 + 展示 sidecar）：**

- `name`：机器 id（= 目录名），kebab-case，**勿改成中文**
- `display_name`：中文场景名（与 catalog 一致；**双写**保留）
- `description`：一行中文路由文案
- `version`：semver
- `_skillhub_meta.json`：WorkBuddy 列表标题（`name`=中文，`source=skillhub`）
- `agents/openai.yaml`：Codex UI（`interface.display_name` = 同一中文名）

## 安装本技能（首装）

**优先路径 A — 官方 pack：**

```bash
curl -fsSL "https://open.winmale.com/api/skills/wm-skillhub/pack" -o /tmp/wm-skillhub.zip
mkdir -p "<skills_root>"
unzip -o /tmp/wm-skillhub.zip -d "<skills_root>"
```

写入 `{skills_root}/wm-skillhub/.wm-skill-meta.json`：

```json
{ "id": "wm-skillhub", "version": "1.0.14", "installed_at": "<ISO8601>" }
```

确认 pack 内已有 `_skillhub_meta.json` 与 `agents/openai.yaml`。

**路径 B（无 shell）：** 从 `https://open.winmale.com/install/skillhub.md` 复制围栏正文，并补写上述 sidecar。

然后做「验收门禁」（见下）。

## 管理子技能

### 列出远端

`GET https://open.winmale.com/api/skills`  
过滤 `visibility` 非 `internal`/`partner`。展示 `id` / `name` / `version` / `summary`。  
同响应含 `roles[]`（`kind: role`）；也可 `GET /api/roles`。Role **不可** `skills/run`，只按正文编排子技能。

### 安装某个技能

**路径 A（推荐）：** catalog `pack_url` → `unzip -o` 到 skills 根 → 确认 `_skillhub_meta.json` + `agents/openai.yaml` → 写 `.wm-skill-meta.json` → 验收。  
含 `references/` 的包 **必须**走路径 A。

**路径 B（无 shell）：**

1. 读 `https://open.winmale.com/api/install/skills/{id}`
2. 复制 **`wm-skill-md` 围栏内**全文到 `SKILL.md`
3. 写 `_skillhub_meta.json`（中文 `name`）与 `agents/openai.yaml`（`interface.display_name`）
4. 写 `.wm-skill-meta.json`
5. 验收门禁

### 安装某个 Role

**路径与 skill 不同，不要走 `install/skills/{id}`（会 404）。**

1. 从 catalog `roles[]`（或 `GET /api/roles`）取 `id` / `pack_url` / `version`
2. **路径 A（推荐）：** `pack_url` 或 `GET /api/roles/{id}/pack` → `unzip -o` 到 skills 根（顶层 `role-*/`）
3. **路径 B（无 shell）：** 读 `https://open.winmale.com/api/install/roles/{id}`，复制围栏正文到 `SKILL.md`，并按合同写 references
4. 写 `_skillhub_meta.json`、`agents/openai.yaml`、`.wm-skill-meta.json`（**必须**含 `"kind":"role"`）
5. 验收门禁；**禁止**对 Role id 执行 skills run — Role 只编排 allowed_skills（用 `wm.sh run`）

### 验收门禁（每次安装/更新必做）

1. `SKILL.md` 非空 YAML：`name: {id}`、`display_name`、`description`、`version`
2. `_skillhub_meta.json.name` = 中文展示名（WorkBuddy）
3. `agents/openai.yaml` 含同一中文 `interface.display_name`（Codex）
4. 禁止空 frontmatter（`---` 后直接 `# 标题`）

### 检查更新

1. 读本地 `.wm-skill-meta.json`（或 frontmatter `version`）
2. 拉 catalog：同时比对 `skills[]` 与 `roles[]` 的 semver
3. **跳过** `visibility` 为 `deprecated` / `hidden` / `internal` / `partner` 的条目（勿当「可更新列表」推给用户）
4. 若本地仍装着带 `replaced_by` 的旧 Pack（如 `wm-screener-mine` → `wm-screen-index`）：**更新/确保安装 `replaced_by`**，并告知用户旧 id 已下架，可选删除本地旧目录；**不要**再给旧 id 升版本
5. 落后则按对应类型安装流程覆盖 pack（skill → skill pack；role → role pack），并更新 `.wm-skill-meta.json`
6. **本地密钥与标记（硬）**
   - 官方 zip **不含**凭证；`unzip -o` **只覆盖** pack 内文件（`SKILL.md` / manifest / sidecar / references…）
   - 凭证与 token 在 **`~/.winmale/`**；升级**不得**改写该目录，除非用户明确要求轮换密钥
   - 若仍发现遗留 `wm-skillhub/.env`：迁到 `~/.winmale/credentials.env` 后可删技能目录内副本（`wm-auth.sh` 也会自动迁）
   - **优先** `bash scripts/update-from-catalog.sh` 或 `mode=update` 升级话术；**禁止**对已有用户态凭证的机器再跑含密钥的首装话术
7. 可先更新本管家，再跑无参 `update-from-catalog.sh`（= `update_all`：**补装**可见 skill/role，含 `opt_in`；**升级**落后包；跳过 deprecated；旧 id 有 `replaced_by` / 别名时装新 id）
8. 抽查 frontmatter / `_skillhub_meta.json`；损坏则改走 pack

### 路由

**意图匹配顺序（硬）：**

1. 先对照已装 **四 Role** 的 `description` / 何时启用（研究/研读/备忘 → 公司深读；关注/提醒/自选 → 投研管家；短核对/贵贱/公告 → 个股核对；开放分析/行业格局/**指数按企业类型看估值结构或多年趋势** → 金融分析师）
2. 再匹配 L1 `wm-*`（`wm-index` / `wm-industry` 为域入口；`wm-*-members` 为窄场景成分快照，**不能**代替金融分析师做分类型 PE·PB）
3. 「研究一下 / 生意全貌+风险 / 进一步研读 / 读财务分析」→ **禁止**只跑 `wm-company-card` + 通读本管家；须走对应 Role（深读须 `wm-analysis-nav`→`run`）
4. 未装 → 确认后安装再调用
5. **禁止**用 tongzhou / 东方财富等外站数据技能冒充平台指数/估值证据

## 常用子技能（摘要）

| id | 用途 |
|----|------|
| `wm-finance-router` | **金融总路由与红线**（投研场景优先加载） |
| `wm-discover` | 发现代码 / 指标 / 策略 / skill；**vfunc 含 `ex`/`call_spec`/`returns_shape` 与域库** |
| `wm-quote-snapshot` | ~~行情快照~~（已下架，请用 company-card） |
| `wm-company-card` | 公司一页纸（含行情；`include` 裁剪） |
| `wm-index` | **指数域总入口**（点位/K线/中枢/成分/权重）；勿与 `wm-screen-index` 混淆 |
| `wm-industry` | **行业域总入口**（中枢/成分/龙头；一期无点位K） |
| `wm-industry-members` | 申万行业成分窄场景（总入口优先 `wm-industry`） |
| `wm-index-members` | 指数成分窄场景（总入口优先 `wm-index`）；分类型/多年结构 → 金融分析师 |
| `wm-analysis-nav` / `wm-analysis-run` | 分析脚本导航与执行 |
| `wm-company-business` | 生意解读卡 |
| `wm-notice-radar` | 公告 / 减持回购；**库主人 `sys/notice.*`**；超出→eval |
| `wm-screen-index` | 统一选股（search/conditions/list·run·save）；字段对齐优先 discover `screener`；索引缺口→分析师+eval（禁第三方选股） |
| `wm-screener-mine` | ~~我的选股~~（已下架，并入 screen-index） |
| `wm-watchlist` | 我的关注；**库主人 `watchlist.*`**；池内再筛→eval/screen |
| `wm-reminder` | 提醒 list/create；**库主人 `reminder.*`**；改删查触发→诚实缺口/eval |
| `wm-cashflow-quality` / `wm-debt-safety` / `wm-revenue-profit` / `wm-statements` / `wm-data` / `wm-dividend-quality` / `wm-shareholder-structure` / `wm-executives` / `wm-operating-segments` | 财务与股权卡片；**三表多期**用 `wm-statements`；**综合查数**用 `wm-data`；股息另见 **`sys/bonus.*`** |
| `wm-xs` | **沙箱 XS**（凡写 XS 用它；常由金融分析师编排） |
| `role-fundamentals-check` | Role：个股核对专家 |
| `role-retail-tracker` | Role：投研管家 |
| `role-company-research-memo` | Role：公司深读专家 |
| `role-financial-analyst` | Role：金融分析师（分析师 + 懂 XS 的程序员） |

完整列表以 catalog 为准。公开侧不要推荐第二张 XS 语法卡。

**行业 / 指数编码**：`industry.S340501`、`index.hs300`；入参兼容裸码与别名（含 `沪深300` / `CSI 300` / `000300` → `index.hs300`）。

## 禁止

- 来路不明的第三方 zip；官方 `pack_url` 是推荐安装路径
- 把 API Key 写进公开仓库或聊天全文复述
- 未装凭证就假定能调 `skills/run`
- 向开放租户推荐 `wm-xs-author-internal` 或未上架的内部作者工具链
- 留下剥光 frontmatter 的 `SKILL.md`，或 WorkBuddy 缺 `_skillhub_meta.json` 却宣称安装成功
