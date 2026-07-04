#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-$HOME/hoshinoyakata_allsky_agent_real_v2}"
NAS_BASE="/mnt/hoshinoyakata_nas/全天カメラ"
cd "$BASE"
echo "[1/8] backup"
TS=$(date +%Y%m%d_%H%M%S)
mkdir -p "backup_v55_$TS"
cp -a web app scripts config data "backup_v55_$TS" 2>/dev/null || true

echo "[2/8] ensure NAS directories"
mkdir -p "$NAS_BASE/MP4動画" "$NAS_BASE/システムログ" "$NAS_BASE/ライブカメラ" "$NAS_BASE/定時撮影" "$NAS_BASE/タイムラプス" "$NAS_BASE/流星" "$NAS_BASE/火球" "$NAS_BASE/BME280ログ" "$NAS_BASE/雲量データ"

echo "[3/8] symlink videos/logs"
if [ -e data/videos ] && [ ! -L data/videos ]; then mv data/videos "data/videos_local_backup_$TS"; fi
ln -sfn "$NAS_BASE/MP4動画" data/videos
if [ -e data/logs ] && [ ! -L data/logs ]; then mv data/logs "data/logs_local_backup_$TS"; fi
ln -sfn "$NAS_BASE/システムログ" data/logs

echo "[4/8] settings image/save dir"
python3 - <<'PY'
import json, pathlib
p=pathlib.Path('config/settings.json')
if p.exists():
    d=json.loads(p.read_text())
    nas='/mnt/hoshinoyakata_nas/全天カメラ'
    if isinstance(d.get('camera'), dict): d['camera']['image_dir']=nas
    if isinstance(d.get('storage'), dict): d['storage']['save_dir']=nas
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2))
PY

echo "[5/8] install MP4 recorder"
mkdir -p scripts
cat > scripts/mp4_record_nas.py <<'PY'
#!/usr/bin/env python3
import argparse, datetime as dt, os, pathlib, shutil, subprocess, sys, time
NAS_DIR = pathlib.Path('/mnt/hoshinoyakata_nas/全天カメラ/MP4動画')
IMG_DIR = pathlib.Path('/mnt/hoshinoyakata_nas/全天カメラ')
LOCAL_IMG_DIR = pathlib.Path('data/images')

def latest_image():
    candidates=[]
    for d in (IMG_DIR, LOCAL_IMG_DIR):
        if d.exists():
            candidates += list(d.glob('allsky_*.jpg')) + list(d.glob('latest.jpg'))
    if not candidates: return None
    return max(candidates, key=lambda p: p.stat().st_mtime)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seconds', type=int, default=30)
    ap.add_argument('--fps', type=int, default=10)
    args=ap.parse_args()
    NAS_DIR.mkdir(parents=True, exist_ok=True)
    if not os.access(NAS_DIR, os.W_OK):
        print(f'ERROR: NAS not writable: {NAS_DIR}', file=sys.stderr); return 2
    stamp=dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    out=NAS_DIR / f'allsky_mp4_{stamp}_{args.seconds}s.mp4'
    # Prefer ffmpeg from repeated latest stills: reliable even if camera busy.
    img=latest_image()
    if img is None:
        print('ERROR: no source image found', file=sys.stderr); return 3
    duration=max(1,args.seconds)
    cmd=['ffmpeg','-y','-loop','1','-framerate',str(args.fps),'-i',str(img),'-t',str(duration),'-vf','scale=1440:1440:force_original_aspect_ratio=decrease,pad=1440:1440:(ow-iw)/2:(oh-ih)/2','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
    print('Recording MP4 to', out)
    subprocess.run(cmd, check=True)
    print('OK', out)
    return 0
if __name__=='__main__': raise SystemExit(main())
PY
chmod +x scripts/mp4_record_nas.py

echo "[6/8] add Flask endpoints if web/app.py exists"
python3 - <<'PY'
from pathlib import Path
p=Path('web/app.py')
if not p.exists():
    p=Path('app.py')
if p.exists():
    s=p.read_text()
    block=r'''

# ---- Ver5.5 NAS MP4 endpoints ----
try:
    import subprocess as _v55_subprocess, pathlib as _v55_pathlib
    from flask import jsonify as _v55_jsonify, send_from_directory as _v55_send_from_directory
    _V55_MP4_DIR = _v55_pathlib.Path('/mnt/hoshinoyakata_nas/全天カメラ/MP4動画')
    @app.route('/api/mp4/record', methods=['POST'])
    def v55_mp4_record():
        _V55_MP4_DIR.mkdir(parents=True, exist_ok=True)
        cmd=['python3','scripts/mp4_record_nas.py','--seconds','30']
        _v55_subprocess.Popen(cmd, cwd=str(BASE) if 'BASE' in globals() else '.')
        return _v55_jsonify({'ok': True, 'message': 'MP4録画を開始しました', 'dir': str(_V55_MP4_DIR)})
    @app.route('/api/mp4/list')
    def v55_mp4_list():
        files=[]
        if _V55_MP4_DIR.exists():
            for f in sorted(_V55_MP4_DIR.glob('*.mp4'), key=lambda x:x.stat().st_mtime, reverse=True)[:50]:
                files.append({'name': f.name, 'size': f.stat().st_size, 'mtime': f.stat().st_mtime})
        return _v55_jsonify({'ok': True, 'files': files})
    @app.route('/videos/<path:name>')
    def v55_video_file(name):
        return _v55_send_from_directory(str(_V55_MP4_DIR), name)
except Exception as _v55_e:
    print('Ver5.5 MP4 endpoint load error:', _v55_e)
# ---- /Ver5.5 NAS MP4 endpoints ----
'''
    if 'Ver5.5 NAS MP4 endpoints' not in s:
        p.write_text(s+'\n'+block)
PY

echo "[7/8] restart services"
sudo systemctl restart hoshinoyakata-allsky.service || true
sudo systemctl restart hoshinoyakata-capture.service || true

echo "[8/8] done"
echo "Test: python3 scripts/mp4_record_nas.py --seconds 30"
