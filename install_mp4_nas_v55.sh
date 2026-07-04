#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(pwd)"
NAS_BASE="/mnt/hoshinoyakata_nas/全天カメラ"
VIDEO_DIR="$NAS_BASE/MP4動画"
LOG_DIR="$NAS_BASE/システムログ"

if [ ! -d "$NAS_BASE" ]; then
  echo "ERROR: NAS folder not found: $NAS_BASE"
  echo "先にNASをマウントしてください。"
  exit 1
fi

mkdir -p "$VIDEO_DIR" "$LOG_DIR"

echo "[1/5] ffmpeg確認"
if ! command -v ffmpeg >/dev/null 2>&1; then
  sudo apt update
  sudo apt install -y ffmpeg
fi

echo "[2/5] scripts配置"
mkdir -p scripts
cp -f "$(dirname "$0")/scripts/mp4_record_nas.py" scripts/mp4_record_nas.py
chmod +x scripts/mp4_record_nas.py

echo "[3/5] data/videos と data/logs をNASへリンク"
mkdir -p data
if [ -e data/videos ] && [ ! -L data/videos ]; then
  mv data/videos "data/videos_local_backup_$(date +%Y%m%d_%H%M%S)"
fi
ln -sfn "$VIDEO_DIR" data/videos

if [ -e data/logs ] && [ ! -L data/logs ]; then
  mv data/logs "data/logs_local_backup_$(date +%Y%m%d_%H%M%S)"
fi
ln -sfn "$LOG_DIR" data/logs

echo "[4/5] settings.jsonへ video_dir/log_dir を追記"
python3 - <<'PY'
import json, pathlib, time
p = pathlib.Path('config/settings.json')
if p.exists():
    data = json.loads(p.read_text(encoding='utf-8'))
    bak = p.with_name(f'settings_backup_v55_{time.strftime("%Y%m%d_%H%M%S")}.json')
    bak.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    data.setdefault('storage', {})
    data['storage']['save_dir'] = '/mnt/hoshinoyakata_nas/全天カメラ'
    data['storage']['video_dir'] = '/mnt/hoshinoyakata_nas/全天カメラ/MP4動画'
    data['storage']['log_dir'] = '/mnt/hoshinoyakata_nas/全天カメラ/システムログ'
    data.setdefault('camera', {})
    data['camera']['image_dir'] = '/mnt/hoshinoyakata_nas/全天カメラ'
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print('settings.json updated')
else:
    print('settings.json not found; skipped')
PY

echo "[5/5] 動作確認"
ls -ld "$NAS_BASE" "$VIDEO_DIR" "$LOG_DIR"
ls -l data/videos data/logs

echo ""
echo "インストール完了。次で30秒録画テストできます:"
echo "./scripts/mp4_record_nas.py --seconds 30"
