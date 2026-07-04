# 星の館 全天カメラ Ver5.5 NAS Complete

## 目的
- 静止画、動画、ログをUGREEN NASへ保存
- MP4録画テスト用スクリプトを追加
- 既存の `data/videos` と `data/logs` をNASへシンボリックリンク

## インストール
ラズパイでプロジェクトフォルダに移動してから:

```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
chmod +x install_v55_complete.sh
./install_v55_complete.sh
```

## MP4録画テスト
```bash
python3 scripts/mp4_record_nas.py --seconds 30
ls -lt "/mnt/hoshinoyakata_nas/全天カメラ/MP4動画" | head
```

## 注意
既存フォルダは `backup_v55_日時` と `data/videos_local_backup_日時` などに退避します。
