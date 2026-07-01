#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
sudo apt update
sudo apt install -y python3-venv python3-pip python3-opencv python3-pil i2c-tools
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
chmod +x scripts/start.sh
mkdir -p data/images data/videos data/events logs
python3 - <<'PY'
from app.camera import capture_still
capture_still()
print('初期画像を作成しました')
PY
cat <<'MSG'

インストール完了。
起動するには：
./scripts/start.sh

ブラウザ：
http://このラズパイのIPアドレス:5000
MSG
