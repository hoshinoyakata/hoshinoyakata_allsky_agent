# 星の館 全天カメラ AIエージェント v2.2

## v2.2 修正
- BME280読み取りを強化
- 0x76 / 0x77 を自動判定
- bus 1 / 10 / 13 / 14 を自動確認
- BME280のエラー内容を画面に表示
- rpicam-still / rpicam-vid 対応継続
- 魚眼ガイドON/OFFボタン追加
- 保存画像表示を安定化

## 更新
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
```

## BME確認
```bash
bash scripts/check_bme280.sh
```
