# Security Policy

## Reporting

If you believe you have found a security issue in these skill packs or related install scripts, please email **support@yamaltech.cn** (do not open a public issue with secrets or exploit details).

## What this repo contains

- Agent skill instructions (`SKILL.md`) and display sidecars
- Marketplace / plugin manifests for Cursor, Claude Code, and Codex

## What this repo does **not** contain

- API keys, tokens, or `.env` files
- Production database credentials
- Exploit or attack tooling

## Safe use

1. Obtain an API key only from [open.winmale.com](https://open.winmale.com).
2. Store credentials in your local agent skill directory (for example `wm-skillhub/.env`); never commit them.
3. Review skill instructions before enabling implicit invocation in production workflows.
4. Prefer installing from this GitHub repository or the WinMale CDN pack URLs published in the official catalog.

## Updates

Skill content is projected from the internal SkillHub source. After updating, re-run your client’s skill/plugin update flow (or `npx skills update`).
