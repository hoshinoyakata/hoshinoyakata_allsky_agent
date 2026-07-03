# 星の館 全天カメラ AIエージェント Ver.2.6 Ultimate Fit

1920×1080表示の最終微調整版です。

## Ver2.6の修正
- ライブビューは正方形
- 全天円を正方形内の約96%まで拡大
- 円が切れない `object-fit: contain`
- 余白を減らした1920×1080専用レイアウト
- Ver.2.5で小さかった魚眼画像を大きく表示

## ラズパイ更新
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```

ブラウザで Ctrl + F5。
