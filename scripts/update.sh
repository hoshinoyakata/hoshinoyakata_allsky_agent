#!/usr/bin/env bash
set -e
cd ~/hoshinoyakata_allsky_agent
git pull || true
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart hoshinoyakata-allsky
