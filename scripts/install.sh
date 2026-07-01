#!/usr/bin/env bash
set -e
cd /home/pi/hoshinoyakata_agent
python3 -m venv venv --system-site-packages || true
venv/bin/pip install -r requirements.txt
chmod +x scripts/*.sh
sudo cp systemd/hoshinoyakata-allsky.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hoshinoyakata-allsky
sudo systemctl restart hoshinoyakata-allsky
