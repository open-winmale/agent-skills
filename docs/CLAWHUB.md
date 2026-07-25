# ClawHub 发布清单（OpenClaw）

面向 [ClawHub](https://clawhub.ai)（OpenClaw 公共技能注册中心）。本仓技能已是标准 `SKILL.md`，可直接用 CLI 发布旗舰条目。

## 重要约束

- ClawHub 上架技能按平台规则以 **MIT-0** 再分发（可自由使用/修改/再分发、无需署名）。  
  若与公司法务冲突，**先停、改协议或只发非敏感说明技能**，再发布。
- 技能正文会公开；**禁止**带 Key、内网 URL、未脱敏样例。
- 运行仍依赖 [open.winmale.com](https://open.winmale.com) API Key；在 SKILL / 描述里写清。

## 建议首发（2 个）

| 本地路径 | 建议 slug | 显示名 |
|----------|-----------|--------|
| `skills/wm-skillhub` | `wm-skillhub` | SkillHub 管家 |
| `skills/wm-company-card` | `wm-company-card` | 公司卡片 |

验证通过后再批量：`wm-valuation`、`wm-watchlist`、`wm-screen-index` 等。

## 步骤

```bash
# 0. CLI（若未装）
npm i -g clawhub --registry=https://registry.npmjs.org

# 1. 登录（须本机浏览器 / token；Agent 无法代登）
clawhub login
# 或: clawhub login --token '<CLAWHUB_TOKEN>'
clawhub whoami

# 2. 干跑（不上传）
cd /Users/jerry/yepless/open/agent-skills
clawhub skill publish ./skills/wm-skillhub \
  --slug wm-skillhub \
  --name "SkillHub 管家" \
  --version 1.0.29 \
  --changelog "WinMale official hub skill" \
  --dry-run

clawhub skill publish ./skills/wm-company-card \
  --slug wm-company-card \
  --name "公司卡片" \
  --version 1.2.9 \
  --changelog "WinMale company snapshot card" \
  --dry-run

# 3. 确认无误后去掉 --dry-run 正式发布
```

**进度（2026-07-25）**

| 项 | 状态 |
|----|------|
| CLI | 已装 |
| 登录 | JerryZhou |
| `wm-skillhub@1.0.29` | 已发布 → https://clawhub.ai/skills/wm-skillhub |
| `wm-company-card@1.2.9` | 已发布 → https://clawhub.ai/skills/wm-company-card |
| 审核 | `verdict: clean`，仍 `pending.publication`（页可开，搜索可能暂不可见） |

安装（公开后）：

```bash
clawhub install wm-skillhub
clawhub install wm-company-card
```

版本号与 `skills/*/manifest.json` → `version` 对齐（见 `SYNC_MANIFEST.json`）。

## 组织号（可选）

若已有 ClawHub org：

```bash
clawhub skill publish ./skills/wm-skillhub --owner <org> --slug wm-skillhub ...
```

## 用户安装

```bash
clawhub install wm-skillhub
clawhub install wm-company-card
```

或继续用本仓 / 官方 pack 解压到 `~/.openclaw/skills/`。

## CI（可选后续）

ClawHub 提供可复用 workflow：`openclaw/clawhub/.github/workflows/skill-publish.yml`  
需仓库 Secret：`CLAWHUB_TOKEN`。首发建议先人工 `dry-run` + 正式发，再接 CI。

## 验收

- [ ] `clawhub search winmale` 或 slug 能搜到  
- [ ] 公开页可查看 SKILL.md、无密钥  
- [ ] OpenClaw 会话能加载并按管家指引配置 API Key  
