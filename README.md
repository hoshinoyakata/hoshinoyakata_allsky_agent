# Ver.2.8 Round True Fit Patch

青い線が楕円になる原因は、全画面表示時にライブビュー自体が16:9へ伸びていたことです。

## 修正内容
- viewer の中に skyStage という正方形ステージを追加
- 画像、青いガイド円、N/E/S/W をすべて skyStage 内に配置
- 全画面表示でも skyStage は `min(94vw, 94vh)` で真四角を維持
- 青いガイド円は楕円にならず、真円になります

## 更新方法
GitHubへ上書き → Commit → Push → ラズパイで
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```
ブラウザは Ctrl + F5。
