# 星の館 AllSky AIエージェント Ver.1.0 開発版

Raspberry Pi 5 + Pi Camera 用の全天カメラWebアプリです。

## 起動
```bash
cd ~/hoshinoyakata_agent
git pull
python3 -m venv venv --system-site-packages
venv/bin/pip install -r requirements.txt
venv/bin/python3 app.py
```

ブラウザで `http://192.168.1.20:5000` を開きます。

## できること
- ライブ画像表示
- ワンクリック撮影・JPEG保存
- 最新画像一覧
- 月齢表示
- 雲量の簡易AI解析
- BME280表示枠（未接続時は準備中）
- SQM表示枠（未接続時は準備中）
- GitHub更新ボタン

## 自動更新サービス準備
`scripts/install_autoupdate.sh` は次版でsystemd登録まで行います。
