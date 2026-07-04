# 星の館 全天カメラ Ver5.6 Stable Whiteout Fix

目的:
- 白飛びした星空モードを安全側へ戻す
- `live_capture_loop.py` の 1.8秒/20dB 固定値を安全値へ変更
- NAS保存リンクを維持
- MP4録画スクリプトをNAS対応版へ更新

使い方:
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
chmod +x install_v56_stable_whitefix.sh
./install_v56_stable_whitefix.sh
sudo systemctl restart hoshinoyakata-capture.service
sudo systemctl restart hoshinoyakata-allsky.service
```

MP4テスト:
```bash
python3 scripts/mp4_record_nas.py --seconds 30
```
