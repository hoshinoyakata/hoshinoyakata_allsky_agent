# 星の館 全天カメラ AIエージェント Ver.3.2 Night AI Pro LED Ghost

内部LAN/PoEパイロットランプの緑反射を軽減する版です。

## 追加内容
- 夜間LEDゴースト軽減
- 緑かぶり補正
- ホットピクセル除去
- 夜間コントラスト補正
- 星空感度 AUTO/LOW/MEDIUM/HIGH/EXTREME/DAY
- 処理後画像は `_nightai.jpg` として保存

## 大事
ソフトでかなり軽減できますが、完全除去はケース内部LEDの遮光が一番効きます。
黒ビニールテープ、黒アルミテープ、黒フェルトなどでLAN/PoE LEDを隠してください。

## 更新方法
GitHubへ上書き → Commit → Push → ラズパイで

```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```

ブラウザで Ctrl + F5。
