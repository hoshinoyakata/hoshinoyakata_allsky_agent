# 星の館 AllSky AIエージェント Ver.1.2-dev

## 追加機能
- 観望指数（雲量・雨・湿度・月齢から簡易判定）
- 雨センサー表示枠
- BME280実機読み取り準備
- MP4タイムラプス作成
- GitHub更新ボタン
- systemd自動起動対応

## 更新方法
Windowsでこのフォルダの中身をGitHubフォルダへ上書きして、GitHub DesktopでCommit → Pushしてください。
ラズパイ側は5分以内に自動更新されます。

## 起動確認
```bash
sudo systemctl status hoshinoyakata-allsky
```
