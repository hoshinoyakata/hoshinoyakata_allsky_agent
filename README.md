# 星の館 全天カメラ Ver5.6 NAS MP4 Web Complete

## 内容
- MP4録画エンジン `scripts/mp4_record_nas.py`
- NASの `全天カメラ/MP4動画` へ保存
- `data/videos` と `data/logs` をNASへリンク
- Web画面の「動画録画（準備中）」を動くMP4録画ボタンに変更するAPI/JSパッチ

## ラズパイで実行
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
chmod +x install_v56_complete.sh
./install_v56_complete.sh
sudo systemctl restart hoshinoyakata-allsky.service
sudo systemctl restart hoshinoyakata-capture.service
```

## 手動テスト
```bash
python3 scripts/mp4_record_nas.py --seconds 30
ls -lt "/mnt/hoshinoyakata_nas/全天カメラ/MP4動画" | head
```
