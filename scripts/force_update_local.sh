#!/usr/bin/env bash
set -e
cd ~/hoshinoyakata_allsky_agent_real_v2
cp config/settings.json config/settings_backup_$(date +%Y%m%d_%H%M%S).json 2>/dev/null || true
git fetch --all
git reset --hard origin/main
git clean -fd
bash scripts/install.sh
