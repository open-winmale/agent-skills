# WinMale Agent Skills

赢麻了（WinMale）官方 [Agent Skills](https://agentskills.io) 公开仓。

面向国内常用 AI 编程助手（**WorkBuddy / CodeBuddy / TRAE / 通义灵码 / OpenClaw** 等）及 Cursor、Claude Code、Codex，提供可安装的投研技能包。  
**数据与执行在 WinMale OpenAPI**（[open.winmale.com](https://open.winmale.com)）。本仓只分发技能说明与安装清单，**不含 API Key**。

| | |
|---|---|
| GitHub（对外发现主源） | https://github.com/open-winmale/agent-skills |
| GitLab 镜像（内网 / CI） | `git@code.yepless.cn:end/open/agent-skills.git` |
| 开放平台 / 申请 Key | https://open.winmale.com |

## 快速安装（国内客户端优先）

技能遵循标准 `SKILL.md`。装到对应客户端的 **skills 根目录** 即可（见下表）。推荐用官方 pack / 管家升级；也可用本仓或 `npx skills`。

### 客户端 skills 根（主打）

| 优先级 | 客户端 | skills 根（用户级） | 备注 |
|--------|--------|---------------------|------|
| 1 | **WorkBuddy** | `~/.workbuddy/skills/` | 列表中文标题读 `_skillhub_meta.json.name` |
| 2 | **CodeBuddy** | `~/.codebuddy/skills/` | 腾讯系，与 WorkBuddy 同类 |
| 3 | **TRAE** | `~/.trae-cn/skills/`（项目：`.trae/skills/`） | 亦支持 `.agents/skills/` |
| 4 | **通义 / Qoder（灵码）** | `~/.lingma/skills/` | 项目：`.lingma/skills/` |
| 5 | **OpenClaw** | `~/.openclaw/skills/` 或 `~/.agents/skills/` | |
| 6 | Cursor | `~/.cursor/skills/` | |
| 7 | Claude Code | `~/.claude/skills/` | |
| 8 | Codex | `~/.codex/skills/` 或 `~/.agents/skills/` | UI：`agents/openai.yaml` |
| — | Windsurf / Copilot / Gemini / Cline 等 | 见各客户端文档或 `~/.agents/skills/` | 兼容标准 SKILL.md |

### 一键 / 跨客户端

```bash
# 先装管家（推荐）
npx skills add open-winmale/agent-skills --skill wm-skillhub -g

# 指定客户端目录示例（WorkBuddy）
npx skills add open-winmale/agent-skills --skill wm-skillhub -g -a workbuddy

# 个股核对示例
npx skills add open-winmale/agent-skills --skill wm-company-card -g

# 本仓第一批全部技能
npx skills add open-winmale/agent-skills --all -g
```

亦可用开放平台 pack（不依赖 Git）：

```bash
curl -fsSL "https://open.winmale.com/api/skills/wm-skillhub/pack" -o /tmp/wm-skillhub.zip
mkdir -p ~/.workbuddy/skills   # 按上表换成你的客户端根目录
unzip -o /tmp/wm-skillhub.zip -d ~/.workbuddy/skills
```

### 插件市场（可选）

```text
# WorkBuddy / CodeBuddy（国内优先）
/plugin marketplace add open-winmale/agent-skills
/plugin install winmale-skillhub@open-winmale
/plugin install winmale-stock-check@open-winmale
/plugin install winmale-my-desk@open-winmale

# Claude Code
/plugin marketplace add open-winmale/agent-skills
/plugin install winmale-skillhub@open-winmale

# Codex
codex plugin marketplace add open-winmale/agent-skills
```

Cursor Team：Dashboard → Plugins → Import `https://github.com/open-winmale/agent-skills`

### 开放发现目录

| 渠道 | 说明 |
|------|------|
| [skills.sh](https://skills.sh) | `npx skills add open-winmale/agent-skills`（安装遥测上榜） |
| [SkillsMP](https://skillsmp.com) | 索引公开 GitHub `SKILL.md` |
| [ClawHub](https://clawhub.ai) | OpenClaw 注册中心；发布步骤见 [`docs/CLAWHUB.md`](./docs/CLAWHUB.md) |

更多渠道与投稿状态：[`docs/MARKETPLACES.md`](./docs/MARKETPLACES.md)。

## 第一批插件

| Plugin | 用途 | 含技能 |
|--------|------|--------|
| `winmale-skillhub` | 管家：凭证、目录、升级 | `wm-skillhub` |
| `winmale-stock-check` | 个股核对 | `wm-company-card` `wm-company-business` `wm-valuation` `wm-notice-radar` `wm-dividend-quality` `wm-debt-safety` `wm-cashflow-quality` `wm-revenue-profit` `wm-discover` |
| `winmale-my-desk` | 投研台 | `wm-watchlist` `wm-reminder` `wm-screen-index` `wm-backtest` |

**建议顺序**：先装管家 → 再装「个股核对」或「投研台」。

完整官方目录、Role 与持续升级以 [open.winmale.com](https://open.winmale.com) / SkillHub catalog 为准；本仓为面向各 Agent 的**发现与安装投影**。

## 使用前准备

1. 在 [open.winmale.com](https://open.winmale.com) 开通应用并取得 API Key  
2. 按 `wm-skillhub` 指引写入本机凭证（**勿提交到 Git**）  
3. 在对应客户端中启用 / 刷新技能列表  

无 Key 时只能阅读说明，无法拉行情与基本面。

## 仓库结构

```text
plugins/          # 三个垂直插件（含 skills）
skills/           # 扁平索引，供 npx skills / 多客户端发现
.claude-plugin/ .cursor-plugin/ .agents/plugins/   # 可选 marketplace
plugins.json
scripts/sync-from-skillhub.py
```

从内源同步：

```bash
SKILLHUB_ROOT=/path/to/skillhub python3 scripts/sync-from-skillhub.py
```

## 双源发布

- **GitHub**：对外主源（技能市场提交、skills.sh）  
- **GitLab（code.yepless.cn）**：内网镜像与 CI；与 GitHub 同内容双推  

```bash
git remote -v
# origin    → GitHub
# gitlab    → git@code.yepless.cn:end/open/agent-skills.git
git push origin main && git push gitlab main
```

## 许可与免责

- 本仓库技能文本默认以 **MIT** 许可分发（见 [`LICENSE`](./LICENSE)）  
- 行情与基本面数据的使用权以 WinMale 服务条款与你的 API 授权为准  
- 内容仅供投研辅助，**不构成投资建议**  

安全与反馈：[`SECURITY.md`](./SECURITY.md) · **support@yamaltech.cn**
