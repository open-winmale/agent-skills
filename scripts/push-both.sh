#!/usr/bin/env bash
# Push main to GitHub (origin) and GitLab mirror (gitlab).
set -euo pipefail
cd "$(dirname "$0")/.."
git push origin main
git push gitlab main
echo "pushed origin + gitlab"
