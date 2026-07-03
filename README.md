# Ver.3.4 Balanced UI Fix

星空感度・システム情報の欄ずれを直した版です。

## 修正
- 星空感度を独立パネルに移動
- システム情報を下段横長に整理
- 雨センサー、風速、BME280の文字かぶりを解消
- 環境情報を3×3固定カード化
- 1920×1080向けに全体バランスを再調整

## 更新方法
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```
ブラウザで Ctrl + F5。
