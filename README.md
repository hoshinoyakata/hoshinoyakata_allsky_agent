# 星の館 全天カメラ AIエージェント Ver.2.4 Final Design

最終デザイン版です。

## 内容
- 全天円が画面内に必ず収まる大きめ中央レイアウト
- 右側にBME280・天文情報・直近キャプチャ
- 下部にシステム情報・AI検出ステータス・次回撮影・保存公開状況
- N/E/S/W 方位表示
- ワンクリック撮影・MP4録画・全画面・更新
- BME280自動検出 bus 1/10/13/14、0x76/0x77
- rpicam-still / rpicam-vid 対応

## ラズパイ更新
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```
