#!/usr/bin/env bash
# Push main to GitHub (origin) and GitLab mirror (gitlab).
# Unset HTTP(S) proxies — Cursor/VPN MITM often 403's git SSH CONNECT.
set -euo pipefail
cd "$(dirname "$0")/.."
unset ALL_PROXY all_proxy HTTP_PROXY HTTPS_PROXY http_proxy https_proxy \
  GIT_HTTP_PROXY GIT_HTTPS_PROXY SOCKS_PROXY SOCKS5_PROXY socks_proxy socks5_proxy \
  2>/dev/null || true
git push origin main
git push gitlab main
echo "pushed origin + gitlab"
