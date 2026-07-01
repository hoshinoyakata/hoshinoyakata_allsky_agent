# Hoshinoyakata AllSky AI Agent Ver.0.1

Raspberry Pi 5 + rpicam camera 用の全天カメラWebアプリです。

## 最初のセットアップ

```bash
cd ~/hoshinoyakata_agent
git pull
chmod +x scripts/*.sh
./scripts/install.sh
./scripts/start.sh
```

ブラウザで開く：

```text
http://localhost:5000
```

別PCから：

```text
http://ラズパイのIP:5000
```

## 今できること

- 全天ライブ画像のWeb表示
- 真円表示のUI
- ワンクリック撮影
- 10秒録画テスト
- GitHub経由更新の土台

## 更新

```bash
cd ~/hoshinoyakata_agent
git pull
./scripts/install.sh
./scripts/start.sh
```
