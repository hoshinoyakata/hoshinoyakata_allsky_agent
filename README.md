# 星の館 全天カメラ AIエージェント Ver.3.1 Night AI Ultimate

夜間が真っ暗になる問題に対応した版です。

## 追加内容
- 昼夜自動判定
- 夜は長時間露出 + 高ゲインで撮影
- 星空感度ボタン AUTO / LOW / MEDIUM / HIGH / EXTREME / DAY
- 現在の露出ms・ゲインを左パネルに表示

## 夜間プリセット
- LOW: 0.5秒 / Gain 12
- MEDIUM: 1.0秒 / Gain 18
- HIGH: 1.5秒 / Gain 24
- EXTREME: 2.5秒 / Gain 32

## 更新方法
GitHubへ上書き → Commit → Push → ラズパイで

```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```

ブラウザで Ctrl + F5。
夜空が暗い場合は左の「星空感度」を HIGH → EXTREME の順で試してください。
