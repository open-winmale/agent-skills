# SkillHub 鉴权与执行包装（维护说明）

**Agent 不要直接换票。** 业务调用用 Python（`.sh` 仅为薄壳）：

| 脚本 | 用途 |
|------|------|
| `wm_skill_run.py` / `wm-skill-run.sh` | L1 执行入口（封装 skills run） |
| `wm_discover.py` | `POST /v1/analysis/xs/discover` |
| `wm_hub.py` | Pack 生命周期 list/install/update/enable/disable/rename/cleanup/doctor |
| `../wm-xs/scripts/wm_xs_eval.py` / `wm_xs_check.py` / `wm_xs_fmt.py` | XS eval / check / fmt（纯 Python，无 node） |
| `wm-xs-eval.sh` / `wm-xs-check.sh` / `wm-xs-fmt.sh`（或 `wm.sh xs-*`） | 上表薄壳；fmt 本地无 API |

共享实现：`_wm_runtime.py`（缓存 + 过期刷新 + 401 重试一次）。默认 **omit scope**。

设计见 [SKILL_RUNTIME_KIT.md](../../../docs/design/SKILL_RUNTIME_KIT.md)。

---

## 运行时目录（与技能包分离）

| 用途 | 默认路径 |
|------|----------|
| 凭证 | `~/.winmale/credentials.env` |
| Token 缓存 | `~/.winmale/cache/access_token.json` |
| Hub 别名 | `~/.winmale/hub/aliases.json` |

```text
WINMALE_API_BASE=https://api.winmale.com
WINMALE_CLIENT_ID=...
WINMALE_API_KEY=...    # = OAuth client_secret
```

## wm_auth.py（仅包装 / 运维）

- 缓存未过期（距 `expires_at` > 120s）→ 直接返回 token  
- 否则 form-urlencoded `client_credentials`，**默认不带 scope**  
- `WM_AUTH_FORCE_REFRESH=1` 丢弃缓存  
- `WM_AUTH_VERBOSE=1` 才打印 `wm-auth: cache hit …`（默认静默，避免与 JSON stdout 混在合并捕获里）  
- `--status` 打印是否有效（不打印 token）
