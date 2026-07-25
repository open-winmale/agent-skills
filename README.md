# WinMale Agent Skills

赢麻了（WinMale）官方 [Agent Skills](https://agentskills.io) 公开仓。

面向 **Cursor / Claude Code / Codex / skills.sh** 等客户端，提供可安装的投研技能包。  
**数据与执行在 WinMale OpenAPI**（[open.winmale.com](https://open.winmale.com)）。本仓只分发技能说明与安装清单，**不含 API Key**。

| | |
|---|---|
| GitHub（对外主源） | https://github.com/open-winmale/agent-skills |
| 开放平台 / 申请 Key | https://open.winmale.com |
| 内源 SkillHub | 由 WinMale SkillHub CI 投影同步 |

## 快速安装

### 推荐：skills.sh（跨客户端）

```bash
# 先装管家
npx skills add open-winmale/agent-skills --skill wm-skillhub -g

# 个股核对包内技能（示例）
npx skills add open-winmale/agent-skills --skill wm-company-card -g

# 或安装本仓全部第一批技能
npx skills add open-winmale/agent-skills --all -g
```

### Claude Code

```text
/plugin marketplace add open-winmale/agent-skills
/plugin install winmale-skillhub@open-winmale
/plugin install winmale-stock-check@open-winmale
/plugin install winmale-my-desk@open-winmale
```

### Codex / ChatGPT desktop

```bash
codex plugin marketplace add open-winmale/agent-skills
```

然后在 `/plugins` 中安装 `winmale-skillhub`、`winmale-stock-check`、`winmale-my-desk`。

### Cursor

- **Team Marketplace**：Dashboard → Plugins → Import  
  `https://github.com/open-winmale/agent-skills`
- 或使用上方 `npx skills add` 写入 `~/.cursor/skills/`

## 第一批插件

| Plugin | 用途 | 含技能 |
|--------|------|--------|
| `winmale-skillhub` | 管家：凭证、目录、升级 | `wm-skillhub` |
| `winmale-stock-check` | 个股核对 | `wm-company-card` `wm-company-business` `wm-valuation` `wm-notice-radar` `wm-dividend-quality` `wm-debt-safety` `wm-cashflow-quality` `wm-revenue-profit` `wm-discover` |
| `winmale-my-desk` | 投研台 | `wm-watchlist` `wm-reminder` `wm-screen-index` `wm-backtest` |

**建议顺序**：先装管家 → 再装「个股核对」或「投研台」。

完整官方目录、Role 与持续升级以 [open.winmale.com](https://open.winmale.com) / SkillHub catalog 为准；本仓为面向各 Agent 市场的**发现与安装投影**。

## 使用前准备

1. 在 [open.winmale.com](https://open.winmale.com) 开通应用并取得 API Key  
2. 按 `wm-skillhub` 指引写入本机凭证（**勿提交到 Git**）  
3. 在支持 Agent Skills 的客户端中启用对应技能  

技能调用托管 API / XS；无 Key 时只能阅读说明，无法拉行情与基本面。

## 仓库结构

```text
plugins/
  winmale-skillhub/       # 管家插件
  winmale-stock-check/    # 个股核对
  winmale-my-desk/        # 投研台
skills/                   # 扁平索引，供 npx skills 发现
.claude-plugin/marketplace.json
.cursor-plugin/marketplace.json
.agents/plugins/marketplace.json
plugins.json              # 插件 ↔ 技能映射（投影配置）
scripts/sync-from-skillhub.py
```

从内源同步：

```bash
SKILLHUB_ROOT=/path/to/skillhub python3 scripts/sync-from-skillhub.py
```

## 许可与免责

- 本仓库技能文本默认以 **MIT** 许可分发（见 [`LICENSE`](./LICENSE)）  
- 行情与基本面数据的使用权以 WinMale 服务条款与你的 API 授权为准  
- 内容仅供投研辅助，**不构成投资建议**  

安全说明见 [`SECURITY.md`](./SECURITY.md)。
