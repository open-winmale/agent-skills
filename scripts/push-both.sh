#!/usr/bin/env bash
# Push main to maintenance origin (JerryZhou) + discovery/mirror remotes.
# GitHub SSH often needs local https_proxy (CONNECT to ssh.github.com:443).
# GitLab (code.yepless.cn) must NOT use Cursor/VPN HTTP MITM — unset proxies.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> push origin (JerryZhou maintenance)"
git push origin main

if git remote get-url open-winmale >/dev/null 2>&1; then
  echo "==> push open-winmale (public discovery mirror)"
  git push open-winmale main
fi

echo "==> push gitlab (unset proxies)"
env -u ALL_PROXY -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy \
  -u GIT_HTTP_PROXY -u GIT_HTTPS_PROXY -u SOCKS_PROXY -u SOCKS5_PROXY -u socks_proxy -u socks5_proxy \
  git push gitlab main

echo "pushed origin (+ open-winmale) + gitlab"
