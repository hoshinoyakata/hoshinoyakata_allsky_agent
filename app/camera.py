from pathlib import Path
from datetime import datetime
import subprocess
import shutil
from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parents[1]
IMG_DIR = BASE / "data" / "images"
VID_DIR = BASE / "data" / "videos"
IMG_DIR.mkdir(parents=True, exist_ok=True)
VID_DIR.mkdir(parents=True, exist_ok=True)

def _demo_image(path):
    img = Image.new("RGB", (1280, 720), (5, 8, 20))
    d = ImageDraw.Draw(img)
    d.ellipse((260, 40, 1020, 700), outline=(120, 170, 255), width=4)
    d.text((40, 40), "星の館 全天カメラ - カメラ未接続デモ画像", fill=(230, 240, 255))
    for x, y in [(450,160),(620,220),(780,180),(560,420),(710,510),(850,360),(380,520)]:
        d.ellipse((x-2,y-2,x+2,y+2), fill=(255,255,255))
    img.save(path, quality=92)

def capture_still():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = IMG_DIR / f"allsky_{ts}.jpg"
    cmd = ["rpicam-still", "-o", str(out), "--width", "1920", "--height", "1080", "--timeout", "1000", "--nopreview"]
    if shutil.which("rpicam-still"):
        try:
            subprocess.run(cmd, check=True, timeout=10)
        except Exception:
            _demo_image(out)
    else:
        _demo_image(out)
    latest = IMG_DIR / "latest.jpg"
    try:
        latest.write_bytes(out.read_bytes())
    except Exception:
        pass
    return out

def latest_image():
    latest = IMG_DIR / "latest.jpg"
    if not latest.exists():
        capture_still()
    return latest

def list_recent(limit=8):
    return sorted([p for p in IMG_DIR.glob("allsky_*.jpg")], reverse=True)[:limit]
