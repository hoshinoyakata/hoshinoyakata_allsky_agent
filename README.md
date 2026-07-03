# 星の館 全天カメラ AIエージェント v2.0

## 主な修正
- 楕円ガイド二重表示を修正
- 画像が横長・楕円に見えにくいよう、表示を安定化
- ライブ画像が黒くなってもページ全体は落ちない
- BME280 0x76対応
- BME280未接続でもアプリは起動継続
- 全画面表示・解除ボタン
- 写真撮影
- MP4動画保存の入口
- 月齢、SQM、雲量の表示枠
- KY-024風速計の表示枠
- systemd自動起動対応

## インストール
ラズパイの `/home/pi/hoshinoyakata_allsky_agent_real_v2` に上書きしてください。

その後：

```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
bash scripts/install.sh
```

ブラウザ：
```text
http://192.168.1.20:5000
```
