# 星の館 全天カメラAIエージェント Ver.5.1 Live Stop Fix

## 修正内容
Ver.5.0でLIVE停止ボタンを押しても撮影が止まらない問題を修正しました。

原因:
外部自動撮影サービス `hoshinoyakata-capture` が `config/settings.json` の
`camera.auto_capture_enabled` を見ずに撮影し続けていました。

修正:
- `scripts/live_capture_loop.py` が `auto_capture_enabled` を毎回確認
- LIVE停止時は撮影を停止
- LIVE開始時は撮影を再開
- `data/capture_status.json` に LIVE ON / LIVE停止中 を記録
- 星空モードは従来通り機能

## 更新方法
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
bash scripts/install.sh
```

## 確認方法
1. ブラウザで Ctrl + F5
2. LIVE停止を押す
3. 10秒待つ
4. 直近キャプチャの時刻が進まなければ成功
5. LIVE開始を押す
6. 数秒ごとに時刻が進めば成功

## ターミナル確認
```bash
tail -f ~/hoshinoyakata_allsky_agent_real_v2/data/logs/live_capture.log
```

LIVE停止で `LIVE disabled - capture paused`、
LIVE開始で `LIVE enabled` が出ます。
