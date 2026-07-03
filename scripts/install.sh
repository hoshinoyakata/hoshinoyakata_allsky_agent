#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
sudo cp systemd/hoshinoyakata-allsky.service /etc/systemd/system/hoshinoyakata-allsky.service
sudo systemctl daemon-reload
sudo systemctl enable hoshinoyakata-allsky
sudo systemctl restart hoshinoyakata-allsky
echo "インストール完了"
echo "ブラウザで開く： http://$(hostname -I | awk '{print $1}'):5000"
