# 星の館 全天カメラ Ver5.5 NAS MP4対応パッチ

## 目的
既に成功している NAS 静止画保存に加えて、MP4動画・システムログも NAS に保存するためのパッチです。

## 保存先
- 静止画: `/mnt/hoshinoyakata_nas/全天カメラ`
- MP4動画: `/mnt/hoshinoyakata_nas/全天カメラ/MP4動画`
- システムログ: `/mnt/hoshinoyakata_nas/全天カメラ/システムログ`

## インストール
ラズパイの `~/hoshinoyakata_allsky_agent_real_v2` にこのフォルダを置いて、以下を実行します。

```bash
chmod +x install_mp4_nas_v55.sh
./install_mp4_nas_v55.sh
```

## MP4録画テスト
```bash
./scripts/mp4_record_nas.py --seconds 30
ls -lt "/mnt/hoshinoyakata_nas/全天カメラ/MP4動画" | head
```

## 仕組み
`latest.jpg` を一定間隔で集め、ffmpegでMP4化します。カメラを直接奪わないため、現在のライブ配信を止めにくい安全方式です。

## 注意
NASがマウントされていない場合はエラーで停止します。先に `/mnt/hoshinoyakata_nas/全天カメラ` が見える状態にしてください。
