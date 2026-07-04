# Ver.4.5 Auto Live Capture

## 重要な修正
Ver.4.4までは、ブラウザが2秒ごとに「新しい画像があるか」を確認するだけでした。
サーバー側で新しい画像を撮影していなければ、最終画像時刻も画面も変わりません。

Ver.4.5では、ラズパイ側のFlaskアプリに自動撮影ループを追加しました。

## 変更点
- LIVE ON中はサーバー側で自動撮影
- 標準では5秒ごとに新しいjpgを保存
- ブラウザは2秒ごとに確認し、新しい画像があれば自動差し替え
- 全画面表示中も自動更新
- 左パネルに「自動撮影 5秒ごと」を表示
- 手動のワンクリック撮影も継続
- 古い画像は一定数を超えると自動整理
- Ver.4.4の全画面最大化、Ver.4.3のキャッシュ対策、Ver.4.2の気圧補正は継承

## 更新方法
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```

## 確認
ブラウザで Ctrl + F5。
右上に `Ver.4.5 Auto Live Capture` と出れば成功です。

## 本当に自動撮影しているか確認
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
ls -lt data/images | head
```
この時刻が5秒ごと前後で進めばOKです。

## 間隔を変える
`config/settings.json` の `live_capture_seconds` を変更してください。
例: 3秒、5秒、10秒。
