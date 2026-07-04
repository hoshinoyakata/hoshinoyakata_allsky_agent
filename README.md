# Ver.4.3 Live Refresh Fix

## 修正内容
- 画面の全天画像が自動更新しない問題を修正
  - ファイル名だけでなく `mtime`（更新時刻）も見て画像を差し替え
  - 2秒ごとに `/api/status` を no-cache で確認
  - 画像URLに `mtime` と `ts` を付けてブラウザキャッシュを回避
- 直近キャプチャの「10分前/20分前/30分前/40分前」の固定表示を廃止
  - 実際の保存時刻を表示
  - 何秒前/何分前も表示
- Ver.4.2の気圧補正（標高108m・raw 712.9対策）は継承

## 更新方法
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```

## 確認
ブラウザで Ctrl + F5。
画面右上に `Ver.4.3 Live Refresh Fix` と出れば成功です。
