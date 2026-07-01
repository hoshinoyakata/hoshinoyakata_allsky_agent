# 星の館 AllSky AIエージェント Ver.1.1-dev

## 追加機能
- MP4タイムラプス作成ボタン
- 雲量の簡易AI解析
- BME280実機読み取り準備
- 月齢・SQM表示
- GitHub更新ボタン
- systemd常駐、自動再起動

## ラズパイ側
既にサービス設定済みなら、GitHub DesktopでPush後、5分以内に自動更新されます。
手動更新する場合:

```bash
cd ~/hoshinoyakata_agent
git pull
venv/bin/pip install -r requirements.txt
sudo systemctl restart hoshinoyakata-allsky
```

## 開く
http://192.168.1.20:5000
