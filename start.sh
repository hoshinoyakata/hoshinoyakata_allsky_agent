#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
sudo apt update
sudo apt install -y python3-venv git
python3 -m venv venv --system-site-packages
./venv/bin/python -m pip install -r requirements.txt
mkdir -p data/captures data/videos
echo "Install complete. Start with: ./scripts/start.sh"
