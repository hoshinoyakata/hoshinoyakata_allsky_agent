# Ver.4.0 Remote Control

パソコンからLIVE状態を操作できる本格遠隔操作版です。

## LIVE表示
- 緑: LIVE中
- 赤: 録画中
- 白/灰: 停止中
- 黄: 撮影中
- 赤系: エラー

## 追加機能
- LIVE開始 / LIVE停止
- REC開始 / REC停止
- AI ON / OFF
- カメラ再起動ボタン
- 状態に応じてLIVEランプ色を自動変更
- Ver.3.6の1920×1080ワイドUIを継承

## 更新方法
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```

ブラウザで Ctrl + F5。
