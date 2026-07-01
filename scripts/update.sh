#!/usr/bin/env bash
set -e
cd /home/pi/hoshinoyakata_agent
git pull
if [ -d venv ]; then
  venv/bin/pip install -r requirements.txt || true
fi
sudo systemctl restart hoshinoyakata-allsky || true
