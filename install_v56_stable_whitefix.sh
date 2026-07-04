#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"
echo "[v5.6 stable] project: $PROJECT_DIR"

mkdir -p config data data/images data/logs data/videos scripts web app
TS=$(date +%Y%m%d_%H%M%S)

# 1) Backup important files
for f in config/settings.json scripts/live_capture_loop.py web/app.py app/camera.py; do
  if [ -e "$f" ]; then cp -a "$f" "$f.v56stable_backup_$TS"; fi
done

# 2) Restore live_capture_loop from the safest backup if current file was heavily patched
if [ -f scripts/live_capture_loop.py.bak_whitefix ]; then
  echo "[1/6] restoring scripts/live_capture_loop.py from bak_whitefix"
  cp -a scripts/live_capture_loop.py.bak_whitefix scripts/live_capture_loop.py
else
  echo "[1/6] no bak_whitefix found; patching current live_capture_loop.py"
fi

# 3) Set sane camera config. Daytime/live safe values to stop whiteout.
echo "[2/6] writing safe camera settings"
python3 - <<'PY'
import json, os
p='config/settings.json'
if os.path.exists(p):
    with open(p, encoding='utf-8') as f:
        d=json.load(f)
else:
    d={}
cam=d.setdefault('camera', {})
cam['night_mode']='auto'
# Conservative exposure/gain defaults. Very low to avoid whiteout; user can raise at night.
cam['night_exposure_us']=30000
cam['night_gain']=1
cam['photo_timeout_ms_day']=500
cam['photo_timeout_ms_night']=800
cam['image_dir']='/mnt/hoshinoyakata_nas/全天カメラ'
st=d.setdefault('storage', {})
st['save_dir']='/mnt/hoshinoyakata_nas/全天カメラ'
st['capture_interval_seconds']=10
st['keep_images']=1200
with open(p,'w',encoding='utf-8') as f:
    json.dump(d,f,ensure_ascii=False,indent=2)
PY

# 4) Patch live_capture_loop.py defaults away from 1.8s/20dB; keep code behavior but safer fallback.
echo "[3/6] patching exposure fallback values"
python3 - <<'PY'
from pathlib import Path
p=Path('scripts/live_capture_loop.py')
if p.exists():
    s=p.read_text(encoding='utf-8')
    repl={
        '1800000':'30000',
        '3000000':'60000',
        '(500000,8,1000)':'(30000,1,800)',
        '(1000000,14,1500)':'(30000,1,800)',
        '(30000,20,2500)':'(30000,1,800)',
        '(60000,20,2500)':'(30000,1,800)',
        'night_gain", 20':'night_gain", 1',
        'night_gain\', 20':'night_gain\', 1',
        'photo_timeout_ms_night", 2500':'photo_timeout_ms_night", 800',
        'photo_timeout_ms_day", 1000':'photo_timeout_ms_day", 500',
    }
    for a,b in repl.items(): s=s.replace(a,b)
    p.write_text(s,encoding='utf-8')
else:
    print('WARN: scripts/live_capture_loop.py not found')
PY

# 5) Ensure NAS dirs and links for videos/logs.
echo "[4/6] preparing NAS folders and symlinks"
NAS_BASE="/mnt/hoshinoyakata_nas/全天カメラ"
if [ -d "$NAS_BASE" ] && [ -w "$NAS_BASE" ]; then
  mkdir -p "$NAS_BASE/MP4動画" "$NAS_BASE/システムログ" "$NAS_BASE/ライブカメラ" "$NAS_BASE/定時撮影" "$NAS_BASE/タイムラプス" "$NAS_BASE/流星" "$NAS_BASE/火球" "$NAS_BASE/BME280ログ" "$NAS_BASE/雲量データ"
  if [ ! -L data/videos ]; then mv data/videos data/videos_local_backup_$TS 2>/dev/null || true; ln -s "$NAS_BASE/MP4動画" data/videos; fi
  if [ ! -L data/logs ]; then mv data/logs data/logs_local_backup_$TS 2>/dev/null || true; ln -s "$NAS_BASE/システムログ" data/logs; fi
else
  echo "WARN: NAS path not writable now: $NAS_BASE"
fi

# 6) Install/update MP4 recorder.
echo "[5/6] installing mp4 recorder"
cp -a scripts/mp4_record_nas.py scripts/mp4_record_nas.py.installed 2>/dev/null || true
cat > scripts/mp4_record_nas.py <<'PY'
#!/usr/bin/env python3
import argparse, os, subprocess, sys, time
from datetime import datetime
from pathlib import Path

NAS_DIR = Path('/mnt/hoshinoyakata_nas/全天カメラ/MP4動画')
LOCAL_DIR = Path('data/videos')

def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seconds', type=int, default=30)
    ap.add_argument('--fps', type=int, default=2)
    args=ap.parse_args()
    outdir = NAS_DIR if NAS_DIR.exists() and os.access(NAS_DIR, os.W_OK) else LOCAL_DIR
    outdir.mkdir(parents=True, exist_ok=True)
    name=f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    out=outdir/name
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] MP4 recording start: {args.seconds}s {args.fps}fps -> {out}", flush=True)
    # Prefer recording from latest.jpg frames, robust with current still-image loop.
    img=Path('/mnt/hoshinoyakata_nas/全天カメラ/latest.jpg')
    if not img.exists(): img=Path('data/images/latest.jpg')
    tmp=outdir/(out.stem+'_frames')
    tmp.mkdir(exist_ok=True)
    frames=[]
    interval=1/max(args.fps,1)
    total=max(args.seconds*args.fps,1)
    for i in range(total):
        if img.exists():
            frame=tmp/f"frame_{i:05d}.jpg"
            try:
                frame.write_bytes(img.read_bytes())
                frames.append(frame)
            except Exception as e:
                print('frame copy error:', e, file=sys.stderr)
        time.sleep(interval)
    if not frames:
        print('ERROR: no frames captured', file=sys.stderr); return 2
    cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-framerate',str(args.fps),'-i',str(tmp/'frame_%05d.jpg'),'-c:v','libx264','-pix_fmt','yuv420p',str(out)]
    r=run(cmd)
    if r.returncode!=0:
        print(r.stderr, file=sys.stderr); return r.returncode
    for f in frames:
        try: f.unlink()
        except: pass
    try: tmp.rmdir()
    except: pass
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] MP4 saved: {out} ({out.stat().st_size} bytes)", flush=True)
    return 0
if __name__=='__main__':
    raise SystemExit(main())
PY
chmod +x scripts/mp4_record_nas.py

# 7) Clear old status if it pins old image dir.
echo "[6/6] clearing old capture status"
rm -f data/capture_status.json

echo "DONE: v5.6 stable whiteout fix installed. Restart services next:"
echo "sudo systemctl restart hoshinoyakata-capture.service"
echo "sudo systemctl restart hoshinoyakata-allsky.service"
