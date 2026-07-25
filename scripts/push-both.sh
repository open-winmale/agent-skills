#!/usr/bin/env bash
# Push main to GitHub (origin) and GitLab mirror (gitlab).
# GitHub SSH often needs local https_proxy (CONNECT to ssh.github.com:443).
# GitLab (code.yepless.cn) must NOT use Cursor/VPN HTTP MITM — unset proxies.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> push origin (GitHub)"
git push origin main

echo "==> push gitlab (unset proxies)"
env -u ALL_PROXY -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy \
  -u GIT_HTTP_PROXY -u GIT_HTTPS_PROXY -u SOCKS_PROXY -u SOCKS5_PROXY -u socks_proxy -u socks5_proxy \
  git push gitlab main

echo "pushed origin + gitlab"
