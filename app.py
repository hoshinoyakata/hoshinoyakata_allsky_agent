from __future__ import annotations

import json, math, os, socket, subprocess, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request, send_from_directory
from PIL import Image, ImageDraw

try:
    import cv2
    import numpy as np
except Exception:
    cv2 = None
    np = None

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
CAPTURES = DATA / "captures"
VIDEOS = DATA / "videos"
CONFIG = BASE / "config" / "settings.json"
CAPTURES.mkdir(parents=True, exist_ok=True)
VIDEOS.mkdir(parents=True, exist_ok=True)

VERSION = "1.1-dev"
app = Flask(__name__)


def load_settings() -> dict[str, Any]:
    default = {"sqm_manual": 20.8, "video_fps": 10, "video_seconds": 10}
    try:
        if CONFIG.exists():
            default.update(json.loads(CONFIG.read_text(encoding="utf-8")))
    except Exception:
        pass
    return default


def moon_age(dt: datetime | None = None) -> float:
    dt = dt or datetime.now(timezone.utc)
    epoch = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
    days = (dt.astimezone(timezone.utc) - epoch).total_seconds() / 86400.0
    return days % 29.53058867


def moon_label(age: float) -> str:
    if age < 1.5: return "新月"
    if age < 7.4: return "上弦へ"
    if age < 8.9: return "上弦の月"
    if age < 14.8: return "満月へ"
    if age < 16.3: return "満月"
    if age < 22.1: return "下弦へ"
    if age < 23.6: return "下弦の月"
    return "新月へ"


def newest_capture() -> Path | None:
    files = sorted(CAPTURES.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def make_demo_image(path: Path) -> None:
    w, h = 1280, 960
    img = Image.new("RGB", (w, h), (8, 18, 32))
    d = ImageDraw.Draw(img)
    cx, cy, r = w // 2, h // 2, min(w, h)//2 - 30
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(18, 26, 42), outline=(0, 200, 255), width=8)
    # stars
    import random
    random.seed(int(time.time()) // 30)
    for _ in range(260):
        a = random.random() * math.tau
        rr = r * math.sqrt(random.random())
        x, y = int(cx + math.cos(a)*rr), int(cy + math.sin(a)*rr)
        c = random.randint(140, 255)
        img.putpixel((x,y),(c,c,c))
    d.text((cx-120, cy-10), "No camera / demo image", fill=(180, 230, 255))
    d.text((40, h-50), datetime.now().strftime("%Y/%m/%d %H:%M:%S"), fill=(220, 240, 255))
    img.save(path, quality=92)


def capture_image() -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = CAPTURES / f"allsky_{ts}.jpg"
    # Try rpicam-still first
    cmd = ["rpicam-still", "-o", str(out), "--timeout", "1000", "--width", "1280", "--height", "960", "--nopreview"]
    try:
        subprocess.run(cmd, check=True, timeout=8, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if out.exists() and out.stat().st_size > 0:
            return out
    except Exception:
        pass
    make_demo_image(out)
    return out


def estimate_cloud_percent(path: Path | None) -> int | None:
    if path is None or cv2 is None or np is None:
        return None
    try:
        img = cv2.imread(str(path))
        if img is None: return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        mask = np.zeros((h,w), dtype=np.uint8)
        cv2.circle(mask, (w//2,h//2), min(w,h)//2-20, 255, -1)
        roi = gray[mask == 255]
        if roi.size == 0: return None
        # simple bright/low-contrast cloud heuristic
        bright = np.mean(roi > 95)
        return int(max(0, min(100, bright * 100)))
    except Exception:
        return None


def read_bme280() -> dict[str, Any]:
    # Optional real BME280 support; returns placeholder if library/sensor not ready
    try:
        import board, busio, adafruit_bme280.basic as adafruit_bme280
        i2c = busio.I2C(board.SCL, board.SDA)
        bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
        return {"ok": True, "temperature": round(bme.temperature,1), "humidity": round(bme.humidity,1), "pressure": round(bme.pressure,1)}
    except Exception as e:
        return {"ok": False, "temperature": None, "humidity": None, "pressure": None, "message": "BME280準備中"}


def create_timelapse() -> Path | None:
    if cv2 is None: return None
    files = sorted(CAPTURES.glob("*.jpg"), key=lambda p: p.stat().st_mtime)[-120:]
    if not files: return None
    first = cv2.imread(str(files[0]))
    if first is None: return None
    h, w = first.shape[:2]
    out = VIDEOS / f"timelapse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"), 10, (w,h))
    for f in files:
        frame = cv2.imread(str(f))
        if frame is None: continue
        if frame.shape[:2] != (h,w): frame = cv2.resize(frame, (w,h))
        writer.write(frame)
    writer.release()
    return out if out.exists() else None


@app.route("/")
def index():
    return render_template("index.html", version=VERSION)

@app.route("/capture", methods=["POST"])
def api_capture():
    p = capture_image()
    return jsonify({"ok": True, "file": p.name, "url": f"/images/{p.name}", "cloud": estimate_cloud_percent(p)})

@app.route("/video", methods=["POST"])
def api_video():
    p = create_timelapse()
    if not p:
        return jsonify({"ok": False, "message": "動画作成には画像またはOpenCVが必要です"})
    return jsonify({"ok": True, "file": p.name, "url": f"/videos/{p.name}"})

@app.route("/status")
def api_status():
    p = newest_capture()
    age = moon_age()
    bme = read_bme280()
    settings = load_settings()
    return jsonify({
        "ok": True,
        "version": VERSION,
        "time": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "hostname": socket.gethostname(),
        "latest": p.name if p else None,
        "latest_url": f"/images/{p.name}" if p else None,
        "cloud": estimate_cloud_percent(p),
        "moon_age": round(age, 1),
        "moon_label": moon_label(age),
        "sqm": settings.get("sqm_manual", 20.8),
        "bme280": bme,
        "captures": [x.name for x in sorted(CAPTURES.glob('*.jpg'), key=lambda z:z.stat().st_mtime, reverse=True)[:8]],
        "videos": [x.name for x in sorted(VIDEOS.glob('*.mp4'), key=lambda z:z.stat().st_mtime, reverse=True)[:5]],
    })

@app.route("/update", methods=["POST"])
def api_update():
    try:
        subprocess.Popen(["bash", "scripts/update.sh"], cwd=str(BASE))
        return jsonify({"ok": True, "message": "更新を開始しました。30秒後に再読み込みしてください。"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})

@app.route("/images/<path:name>")
def images(name):
    return send_from_directory(CAPTURES, name)

@app.route("/videos/<path:name>")
def videos(name):
    return send_from_directory(VIDEOS, name)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
