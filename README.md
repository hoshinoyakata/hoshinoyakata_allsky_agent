# Ver.4.1 Control Final

Ver.4系の遠隔操作完成版です。

## 追加
- LIVE開始 / LIVE停止
- REC開始 / REC停止
- LIVEランプ色連動
  - 緑: LIVE
  - 赤: REC
  - 白/灰: OFFLINE
  - 黄: 撮影中
- 1920×1080ワイドUI継承
- 雲量AI・夜間AI継承

## 通常更新
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```

## git pullが止まる時
```bash
bash scripts/force_update_local.sh
```
