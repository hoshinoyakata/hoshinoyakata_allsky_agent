# Ver.4.2 Pressure Live Fix

- BME280の712.9問題を自動補正します。
- raw値が850未満なら mmHg相当として hPaへ変換します。
- 標高108mで海面更正気圧を表示します。
- ライブ画像を2秒ごとに確認し、最終画像時刻も表示します。

## 更新
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```

## 確認
画面右上に Ver.4.2 Pressure Live Fix と出れば成功です。

## BME280確認
```bash
bash scripts/check_bme280.sh
```
