# Ver.2.9 Fullscreen Center Fit Patch

全画面で少し下が切れ気味になる問題を修正したパッチです。

## 修正内容
- 全画面時の正方形ステージを 88vw/88vh に少し縮小
- 全天画像を 88% に縮小
- ステージを少し上へ移動
- 青いガイド円は真円のまま維持
- N/S/E/W を正方形ステージ内で再配置

## 更新方法
GitHubへ上書き → Commit → Push → ラズパイで
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```
ブラウザは Ctrl + F5。
