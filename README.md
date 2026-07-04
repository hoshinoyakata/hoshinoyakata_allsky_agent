# Ver.4.6 Startup Fix

## 修正内容
Ver.4.5でサービス起動時に落ちる問題を修正しました。

原因:
`start_auto_capture_once()` が起動時に `log()` を呼んでいましたが、
環境によっては `log()` 定義前に実行されて `NameError: name 'log' is not defined` になっていました。

修正:
- 起動直後でも使える `safe_log()` を追加
- 自動撮影スレッド開始ログを `safe_log()` に変更
- Ver.4.5の自動撮影機能は継承
  - LIVE ON中、5秒ごとに自動撮影
  - ブラウザは2秒ごとに自動更新
  - 全画面中も更新

## 更新方法
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```

## 確認
```bash
sudo systemctl status hoshinoyakata-allsky --no-pager -l
```
`active (running)` になればOKです。

ブラウザで Ctrl + F5。
右上に `Ver.4.6 Startup Fix` と出れば成功です。
