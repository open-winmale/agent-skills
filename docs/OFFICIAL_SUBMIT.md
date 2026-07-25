# 官方目录提交（需人工）

Agent 无法代填需登录的官方表单。按下面做即可。

## Claude Plugin Directory（社区目录）

**优先级（国内）**：中低 — 品牌/出海有用；国内主路径不依赖它。

1. 确认仓公开：https://github.com/open-winmale/agent-skills  
2. （可选）本机有 Claude Code 时：`claude plugin validate`  
3. 登录后打开其一：  
   - https://platform.claude.com/plugins/submit  
   - https://claude.ai/admin-settings/directory/submissions/plugins/new  
4. 仓库填：`https://github.com/open-winmale/agent-skills`  
5. 说明建议：赢麻了投研 Agent Skills；需 [open.winmale.com](https://open.winmale.com) API Key；先装 `winmale-skillhub`  
6. 提交后等自动审核；通过后 **push 会自动同步**，无需反复交  

用户不等收录也可：

```text
/plugin marketplace add open-winmale/agent-skills
/plugin install winmale-skillhub@open-winmale
```

## Cursor Marketplace（官方精选）

**优先级（国内）**：中低 — 人工审周期不定。

1. 打开 https://cursor.com/marketplace/publish  
2. 提交仓库：`https://github.com/open-winmale/agent-skills`  
3. 建议主推插件叙事：`winmale-skillhub`（管家）或整仓 marketplace  
4. 等待 Anysphere 审核（可能无「我的提交」列表，只能盯公开 marketplace 搜索）  

不等审也可用：

- Team：Dashboard → Plugins → Import 上述 GitHub URL  
- 或：`npx skills add open-winmale/agent-skills --skill wm-skillhub -g`
