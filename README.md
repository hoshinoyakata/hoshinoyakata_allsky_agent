# Ver.4.7 External Capture Stable

## 重要
Ver.4.5/4.6ではWebアプリの中で自動撮影を回していたため、カメラ側で詰まるとWebサーバーごと落ちる可能性がありました。

Ver.4.7では方式を変えました。

## 変更点
- Web表示サービス: `hoshinoyakata-allsky`
- 自動撮影サービス: `hoshinoyakata-capture`
- 2つのサービスに分離
- 自動撮影が失敗しても、Web画面は落ちにくい
- 標準では5秒ごとに自動撮影
- ブラウザは2秒ごとに最新画像を確認
- 全画面中も自動更新
- Ver.4.4の全画面最大化、Ver.4.3のキャッシュ対策、Ver.4.2の気圧補正を継承

## 更新方法
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
```

## 確認
```bash
sudo systemctl status hoshinoyakata-allsky --no-pager -l
sudo systemctl status hoshinoyakata-capture --no-pager -l
```

両方 `active (running)` ならOKです。

## 自動撮影確認
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
ls -lt data/images | head
```

5秒前後で時刻が進めばOKです。

## 自動撮影だけ止めたい時
```bash
bash scripts/stop_external_capture.sh
```
