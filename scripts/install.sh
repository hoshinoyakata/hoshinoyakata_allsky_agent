#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

sudo cp systemd/hoshinoyakata-allsky.service /etc/systemd/system/hoshinoyakata-allsky.service
sudo cp systemd/hoshinoyakata-capture.service /etc/systemd/system/hoshinoyakata-capture.service

sudo systemctl daemon-reload
sudo systemctl enable hoshinoyakata-allsky
sudo systemctl enable hoshinoyakata-capture

sudo systemctl restart hoshinoyakata-allsky
sudo systemctl restart hoshinoyakata-capture

echo ""
echo "インストール完了"
echo "ブラウザで開く： http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "確認:"
echo "  sudo systemctl status hoshinoyakata-allsky --no-pager -l"
echo "  sudo systemctl status hoshinoyakata-capture --no-pager -l"
