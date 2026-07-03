# 星の館 全天カメラ AIエージェント Ver.2.7 Safe Fit

Ver2.6で魚眼円が入りきらなかったため、表示倍率を安全側に修正した版です。

## 修正点
- ライブビューは正方形のまま
- 魚眼画像の表示倍率を 96% → 86% に変更
- ガイド円も 88% → 78% に変更
- 全天円が切れずに全部入るように余白を確保
- 1920×1080ディスプレイ用レイアウト維持

## ラズパイ更新
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```

更新後はブラウザで Ctrl + F5。
