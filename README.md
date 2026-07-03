# Ver.3.6 Wide 1920 UI

野島さんが指定した1920×1080用の横長完成デザイン版です。

## 変更点
- 1920×1080に合わせた4列×3段のワイド配置
- 右と下の空きスペースを埋める
- 全天画像を中央に大きく表示
- 左にライブ情報・カメラ操作・星空感度
- 右に環境情報・天文情報・AI検出・直近キャプチャ
- 下段にシステム情報・保存公開・ネットワーク・クイック操作

## 更新方法
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```

ブラウザで Ctrl + F5。
