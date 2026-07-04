星の館 全天カメラ Ver.5.4 Storage & Interval Fix

追加内容:
- 保存先を指定可能
- 撮影間隔を指定可能
- LIVE停止/開始はVer.5.3のまま有効
- 保存先が使えない時は本体保存へ自動退避
- 古い画像を自動削除

上書きするファイル:
live_capture_loop.py

上書き先:
/home/pi/hoshinoyakata_allsky_agent_real_v2/scripts/live_capture_loop.py

PowerShell:
scp .\live_capture_loop.py pi@192.168.1.20:/home/pi/hoshinoyakata_allsky_agent_real_v2/scripts/live_capture_loop.py

反映:
ssh pi@192.168.1.20 "sudo systemctl restart hoshinoyakata-capture"

保存先と間隔は config/settings.json の camera に指定します。

例:
"camera": {
  "image_dir": "/home/pi/hoshinoyakata_allsky_agent_real_v2/data/images",
  "live_capture_seconds": 10,
  "keep_images": 1200
}

USB SSD例:
"camera": {
  "image_dir": "/media/pi/ALLSKY/images",
  "live_capture_seconds": 10,
  "keep_images": 5000
}

まずは本体保存のまま live_capture_seconds を 5 または 10 にするのがおすすめです。
