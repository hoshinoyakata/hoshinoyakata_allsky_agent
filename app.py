from __future__ import annotations

import json
import math
import os
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request, send_from_directory

BASE = Path(__file__).resolve().parent
CAPTURES = BASE / "data" / "captures"
VIDEOS = BASE / "data" / "videos"
CAPTURES.mkdir(parents=True, exist_ok=True)
VIDEOS.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
VERSION = "1.0-dev"


def _try_picamera_capture(path: Path) -> bool:
    """Raspberry Pi Camera capture. Falls back cleanly when unavailable."""
    try:
        from picamera2 import Picamera2  # type: ignore

        picam2 = Picamera2()
        config = picam2.create_still_configuration(main={"size": (1920, 1080)})
        picam2.configure(config)
        picam2.start()
        picam2.capture_file(str(path))
        picam2.stop()
        return True
    except Exception as e:
        print(f"picamera capture skipped: {e}")
        return False


def _make_placeholder(path: Path) -> None:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (1200, 1200), (8, 15, 35))
    d = ImageDraw.Draw(img)
    d.ellipse((80, 80, 1120, 1120), outline=(24, 190, 255), width=8)
    d.text((430, 570), "No Camera Image", fill=(210, 235, 255))
    d.text((385, 620), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), fill=(130, 180, 220))
    img.save(path, quality=92)


def latest_capture() -> Path | None:
    files = sorted(CAPTURES.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def moon_age(dt: datetime | None = None) -> float:
    # Simple approximation from known new moon epoch 2000-01-06 18:14 UTC
    dt = dt or datetime.now(timezone.utc)
    epoch = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
    days = (dt - epoch).total_seconds() / 86400.0
    return days % 29.53058867


def moon_label(age: float) -> str:
    if age < 1.5:
        return "新月"
    if age < 7.4:
        return "上弦へ"
    if age < 8.9:
        return "上弦の月"
    if age < 14.8:
        return "満月へ"
    if age < 16.3:
        return "満月"
    if age < 22.1:
        return "下弦へ"
    if age < 23.6:
        return "下弦の月"
    return "新月へ"


def analyze_cloud(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"cloud": None, "message": "画像待ち"}
    try:
        import cv2
        import numpy as np

        img = cv2.imread(str(path))
        if img is None:
            raise RuntimeError("image read failed")
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # Very rough: bright, low saturation areas tend to be cloud/indoor highlights.
        sat = hsv[:, :, 1]
        val = hsv[:, :, 2]
        mask = (val > 110) & (sat < 90)
        cloud = float(np.mean(mask) * 100)
        return {"cloud": round(cloud, 1), "message": "簡易解析"}
    except Exception as e:
        return {"cloud": None, "message": f"解析待ち: {e}"}


def read_bme280() -> dict[str, Any]:
    # Placeholder designed to be safely replaced by real smbus2/BME280 code.
    return {"temperature": None, "humidity": None, "pressure": None, "message": "BME280準備中"}


def git_info() -> dict[str, Any]:
    def run(cmd: list[str]) -> str:
        try:
            return subprocess.check_output(cmd, cwd=BASE, text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            return ""

    return {
        "branch": run(["git", "branch", "--show-current"]),
        "commit": run(["git", "rev-parse", "--short", "HEAD"]),
        "remote": run(["git", "remote", "get-url", "origin"]),
    }


@app.route("/")
def index():
    return render_template("index.html", version=VERSION)


@app.route("/capture", methods=["POST"])
def capture():
    filename = "allsky_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
    path = CAPTURES / filename
    ok = _try_picamera_capture(path)
    if not ok:
        _make_placeholder(path)
    return jsonify({"ok": True, "file": filename, "camera": ok})


@app.route("/image/latest")
def image_latest():
    f = latest_capture()
    if f is None:
        return send_from_directory(BASE / "static", "noimage.svg")
    return send_from_directory(CAPTURES, f.name)


@app.route("/captures/<name>")
def capture_file(name: str):
    return send_from_directory(CAPTURES, name)


@app.route("/api/status")
def status():
    latest = latest_capture()
    age = moon_age()
    cloud = analyze_cloud(latest)
    bme = read_bme280()
    return jsonify({
        "version": VERSION,
        "time": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "hostname": socket.gethostname(),
        "latest": latest.name if latest else None,
        "moon_age": round(age, 1),
        "moon_label": moon_label(age),
        "cloud": cloud,
        "bme280": bme,
        "sqm": {"value": None, "message": "SQM準備中"},
        "git": git_info(),
    })


@app.route("/api/list")
def image_list():
    files = sorted(CAPTURES.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)[:12]
    return jsonify([{"name": p.name, "url": f"/captures/{p.name}", "mtime": datetime.fromtimestamp(p.stat().st_mtime).strftime("%H:%M:%S")} for p in files])


@app.route("/api/update", methods=["POST"])
def update_from_github():
    try:
        out = subprocess.check_output(["git", "pull", "--ff-only"], cwd=BASE, text=True, stderr=subprocess.STDOUT, timeout=60)
        return jsonify({"ok": True, "message": out})
    except subprocess.CalledProcessError as e:
        return jsonify({"ok": False, "message": e.output}), 500
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
