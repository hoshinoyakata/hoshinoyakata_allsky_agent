#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
git pull --ff-only
if [ -x venv/bin/pip ]; then venv/bin/pip install -r requirements.txt; fi
echo "更新完了。必要なら app.py を再起動してください。"
