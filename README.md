# Ver.4.4 Fullscreen Max

## 修正内容
- 全画面表示の全天画像を大きく表示
- 1920×1080画面では高さ方向を最大限使用
- 画像サイズを `min(96vw, 96vh)` に拡大
- 画像そのものを100%表示
- 青い外周リングも画像に合わせて拡大
- ブラウザによって `:fullscreen` が効かない場合に備えて `fullscreen-active` クラスで補助
- Ver.4.3の自動更新修正、Ver.4.2の気圧補正は継承

## 更新方法
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```

## 確認
ブラウザで Ctrl + F5。
画面右上に `Ver.4.4 Fullscreen Max` と出れば成功です。

## 全画面確認
画面内の「全画面表示」ボタンを押してください。
全天画像が画面高さの約96%まで大きく表示されます。
