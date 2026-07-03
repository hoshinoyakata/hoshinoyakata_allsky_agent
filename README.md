# Ver.3.3 UI Weather Fix

## 修正点
- 曇りなのに雲量0%になる問題を修正
  - 夜は星数と空の明るさから雲量推定
  - 昼は従来の画像AI解析
- 星空感度表示の文字かぶりを修正
- 風速を固定値ではなくGPIOから読みに行くように修正
  - 初期設定 GPIO17 / 1回転3パルス
- 雨センサー欄の文字かぶりを修正
  - 初期設定では未接続表示
  - 使う場合は config/settings.json の rain.enabled を true にする

## 更新方法
GitHubへ上書き → Commit → Push → ラズパイで

```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```

ブラウザで Ctrl + F5。
