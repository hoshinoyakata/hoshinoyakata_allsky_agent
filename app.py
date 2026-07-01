from __future__ import annotations

import json
import math
import os
import socket
import subprocess
import time
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
LOGS = BASE / "logs"
CONFIG = BASE / "config" / "settings.json"
for p in (CAPTURES, VIDEOS, LOGS, CONFIG.parent):
    p.mkdir(parents=True, exist_ok=True)

VERSION = "1.2-dev"
app = Flask(__name__, template_folder="templates", static_folder="static")


def load_settings() -> dict[str, Any]:
    default: dict[str, Any] = {
        "sqm_manual": 20.8,
        "video_fps": 10,
        "camera_width": 1280,
        "camera_height": 960,
        "auto_capture_enabled": False,
        "auto_capture_interval_sec": 60,
        "rain_gpio": None,
        "bme280_address": "0x76",
    }
    try:
        if CONFIG.exists():
            default.update(json.loads(CONFIG.read_text(encoding="utf-8")))
    except Exception:
        pass
    return default


def save_settings(data: dict[str, Any]) -> dict[str, Any]:
    settings = load_settings()
    for k in settings.keys():
        if k in data:
            settings[k] = data[k]
    CONFIG.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    return settings


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
    settings = load_settings()
    w = int(settings.get("camera_width", 1280))
    h = int(settings.get("camera_height", 960))
    img = Image.new("RGB", (w, h), (8, 18, 32))
    d = ImageDraw.Draw(img)
    cx, cy, r = w // 2, h // 2, min(w, h)//2 - 30
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(18, 26, 42), outline=(0, 200, 255), width=8)
    import random
    random.seed(int(time.time()) // 30)
    for _ in range(260):
        a = random.random() * math.tau
        rr = r * math.sqrt(random.random())
        x, y = int(cx + math.cos(a)*rr), int(cy + math.sin(a)*rr)
        c = random.randint(140, 255)
        if 0 <= x < w and 0 <= y < h:
            img.putpixel((x, y), (c, c, c))
    d.text((cx-130, cy-10), "No camera / demo image", fill=(180, 230, 255))
    d.text((40, h-50), datetime.now().strftime("%Y/%m/%d %H:%M:%S"), fill=(220, 240, 255))
    img.save(path, quality=92)


def capture_image() -> Path:
    settings = load_settings()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = CAPTURES / f"allsky_{ts}.jpg"
    w = str(settings.get("camera_width", 1280))
    h = str(settings.get("camera_height", 960))
    commands = [
        ["rpicam-still", "-o", str(out), "--timeout", "1000", "--width", w, "--height", h, "--nopreview"],
        ["libcamera-still", "-o", str(out), "--timeout", "1000", "--width", w, "--height", h, "--nopreview"],
    ]
    for cmd in commands:
        try:
            subprocess.run(cmd, check=True, timeout=10, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(mask, (w//2, h//2), min(w, h)//2-20, 255, -1)
        roi = gray[mask == 255]
        if roi.size == 0: return None
        bright = np.mean(roi > 95)
        low_contrast = max(0.0, 1.0 - (float(np.std(roi)) / 60.0))
        score = (bright * 0.75 + low_contrast * 0.25) * 100
        return int(max(0, min(100, score)))
    except Exception:
        return None


def read_bme280() -> dict[str, Any]:
    settings = load_settings()
    address = int(str(settings.get("bme280_address", "0x76")), 16)
    try:
        import board, busio, adafruit_bme280.basic as adafruit_bme280
        i2c = busio.I2C(board.SCL, board.SDA)
        bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=address)
        return {"ok": True, "temperature": round(bme.temperature, 1), "humidity": round(bme.humidity, 1), "pressure": round(bme.pressure, 1)}
    except Exception:
        return {"ok": False, "temperature": None, "humidity": None, "pressure": None, "message": "BME280準備中"}


def read_rain_sensor() -> dict[str, Any]:
    gpio = load_settings().get("rain_gpio")
    if gpio in (None, "", "none"):
        return {"ok": False, "rain": None, "message": "雨センサー未設定"}
    try:
        import gpiozero
        pin = gpiozero.DigitalInputDevice(int(gpio), pull_up=True)
        wet = not bool(pin.value)
        pin.close()
        return {"ok": True, "rain": wet, "label": "雨" if wet else "乾燥"}
    except Exception as e:
        return {"ok": False, "rain": None, "message": f"雨センサー準備中: {e}"}


def observation_score(cloud: int | None, rain: dict[str, Any], bme: dict[str, Any], moon: float) -> dict[str, Any]:
    score = 100
    reasons = []
    if cloud is not None:
        score -= int(cloud * 0.65)
        if cloud > 70: reasons.append("雲が多い")
        elif cloud > 35: reasons.append("雲量やや多め")
    if rain.get("rain") is True:
        score -= 80
        reasons.append("雨検知")
    hum = bme.get("humidity")
    if isinstance(hum, (int, float)) and hum > 85:
        score -= 15
        reasons.append("湿度高め")
    if 10 <= moon <= 20:
        score -= 10
        reasons.append("月明かりあり")
    score = max(0, min(100, score))
    if score >= 80: label = "観望好適"
    elif score >= 55: label = "条件まずまず"
    elif score >= 30: label = "雲に注意"
    else: label = "観望厳しめ"
    return {"score": score, "label": label, "reasons": reasons or ["通常監視中"]}


def create_timelapse() -> Path | None:
    if cv2 is None: return None
    files = sorted(CAPTURES.glob("*.jpg"), key=lambda p: p.stat().st_mtime)[-240:]
    if not files: return None
    first = cv2.imread(str(files[0]))
    if first is None: return None
    h, w = first.shape[:2]
    fps = int(load_settings().get("video_fps", 10))
    out = VIDEOS / f"timelapse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for f in files:
        frame = cv2.imread(str(f))
        if frame is None: continue
        if frame.shape[:2] != (h, w): frame = cv2.resize(frame, (w, h))
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


@app.route("/settings", methods=["GET", "POST"])
def api_settings():
    if request.method == "POST":
        return jsonify({"ok": True, "settings": save_settings(request.json or {})})
    return jsonify({"ok": True, "settings": load_settings()})


@app.route("/status")
def api_status():
    p = newest_capture()
    age = moon_age()
    bme = read_bme280()
    rain = read_rain_sensor()
    cloud = estimate_cloud_percent(p)
    obs = observation_score(cloud, rain, bme, age)
    settings = load_settings()
    return jsonify({
        "ok": True,
        "version": VERSION,
        "time": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "hostname": socket.gethostname(),
        "latest": p.name if p else None,
        "latest_url": f"/images/{p.name}" if p else None,
        "cloud": cloud,
        "moon_age": round(age, 1),
        "moon_label": moon_label(age),
        "sqm": settings.get("sqm_manual", 20.8),
        "bme280": bme,
        "rain": rain,
        "observation": obs,
        "captures": [x.name for x in sorted(CAPTURES.glob('*.jpg'), key=lambda z: z.stat().st_mtime, reverse=True)[:10]],
        "videos": [x.name for x in sorted(VIDEOS.glob('*.mp4'), key=lambda z: z.stat().st_mtime, reverse=True)[:8]],
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
