# 星の館 全天カメラ AIエージェント Ver.2.5 Ultimate Final

1920×1080ディスプレイ専用の最終完成版UIです。

## 主な内容
- ライブビューは正方形
- 全天円が全部入る `object-fit: contain`
- カメラ撮影は 3072×3072 の正方形設定
- 1920×1080画面に収まる最終ダッシュボード
- BME280自動認識
- ワンクリック撮影
- MP4録画
- 全画面表示
- AI検出ステータス表示
- 環境情報・天文情報・保存公開ステータス表示

## ラズパイ更新
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```

ブラウザ：
http://192.168.1.20:5000

更新後は Ctrl + F5 で強制更新してください。
