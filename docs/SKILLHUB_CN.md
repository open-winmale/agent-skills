# SkillHub.cn 发布说明

将本仓 `skills/` 投影同步到国内 Skill 商店 [SkillHub.cn](https://skillhub.cn)。

## 凭证（切勿提交）

本地文件（已 gitignore）：

```bash
# .env.skillhub.cn  (chmod 600)
SKILLHUB_KEY=skh_...
SKILLHUB_HOST=https://api.skillhub.cn
```

也可用环境变量 `SKILLHUB_KEY` / `SKILLHUB_TOKEN`（以及可选 `SKILLHUB_HOST`）。

GitHub Actions 使用 repository secret：`SKILLHUB_KEY`。

## 前置

- CLI：`skillhub`（`~/.local/bin/skillhub` 亦可）
- 安装（仅 CLI）：

```bash
curl -fsSL https://skillhub-1388575217.cos.ap-guangzhou.myqcloud.com/install/install.sh | bash -s -- --cli-only
```

## 用法

```bash
# 本地 + 远端对照
./scripts/publish-skillhub-cn.sh --list

# 预检（CLI --dry-run，不实际上传）
./scripts/publish-skillhub-cn.sh --dry-run

# 发布首批 wm-*（跳过远端已有且 version ≥ 本地）
./scripts/publish-skillhub-cn.sh

# 指定 slug
./scripts/publish-skillhub-cn.sh --only wm-skillhub,wm-company-card

# 强制同版本重发
./scripts/publish-skillhub-cn.sh --force --only wm-skillhub
```

脚本会把 Cursor 风格 frontmatter（`name` / `display_name`）**暂存映射**为 SkillHub 要求的 `slug` / `displayName` / `version`，**不改写**仓库内原始 `SKILL.md`，避免与 `sync-from-skillhub.py` 冲突。
Staging 会排除 SkillHub.cn 不允许的扩展名（当前含 `*.xs`）；仓库内原文件不改动。


去重规则：

1. 按 `slug`：远端 version ≥ 本地 → skip（除非 `--force`）
2. 按 `displayName` 精确匹配：若已有其它 slug 且 version ≥ 本地 → skip（避免重复上传已存在的中文名技能）

成功发布后更新可提交的状态文件：[`SKILLHUB_CN_PUBLISH_STATE.json`](./SKILLHUB_CN_PUBLISH_STATE.json)。

## CI

工作流：`.github/workflows/publish-skillhub-cn.yml`

- `push` 到 `main`（`skills/**`、插件内 skills、发布脚本变更时）
- `workflow_dispatch`
- 无 `SKILLHUB_KEY` secret 时跳过（fork 安全）
- 仅在 `JerryZhou/agent-skills` 或 `open-winmale/agent-skills` 上尝试发布

## 参考

- 安装：https://skillhub.cn/install/skillhub.md
- Agent 发布指南：https://skillhub.cn/ai/release.md
- API host：`https://api.skillhub.cn`
