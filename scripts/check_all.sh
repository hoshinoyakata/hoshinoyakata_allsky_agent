#!/usr/bin/env bash
cd ~/hoshinoyakata_allsky_agent_real_v2
echo "=== Web ==="
sudo systemctl status hoshinoyakata-allsky --no-pager -l | head -25
echo ""
echo "=== Capture ==="
sudo systemctl status hoshinoyakata-capture --no-pager -l | head -25
echo ""
echo "=== Latest images ==="
ls -lt data/images | head
echo ""
echo "=== API ==="
curl -s http://127.0.0.1:5000/api/status | head -c 500
echo ""
