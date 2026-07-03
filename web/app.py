\
from __future__ import annotations

from flask import Flask, jsonify, render_template, send_from_directory
from pathlib import Path
from datetime import datetime, timezone
import json
import subprocess

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
IMG = DATA / "images"
VID = DATA / "videos"
LOG = DATA / "logs"
CONFIG = BASE / "config" / "settings.json"

for p in (IMG, VID, LOG):
    p.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, template_folder="templates", static_folder="static")

def settings():
    with open(CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)

def cmd(command: str, timeout: int = 30):
    return subprocess.run(command, shell=True, text=True, capture_output=True, timeout=timeout)

def latest_file(folder: Path, suffix: str):
    files = sorted(folder.glob(f"*{suffix}"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0].name if files else None

def moon_age():
    epoch = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    days = (now - epoch).total_seconds() / 86400.0
    return round(days % 29.53058867, 1)

def read_bme280():
    cfg = settings().get("bme280", {})
    if not cfg.get("enabled", True):
        return {"ok": False, "message": "BME280 disabled"}
    try:
        from smbus2 import SMBus
        from bme280 import BME280
        bus_no = int(cfg.get("bus", 1))
        addr_raw = cfg.get("address", "0x76")
        address = int(addr_raw, 16) if isinstance(addr_raw, str) else int(addr_raw)
        sensor = BME280(i2c_dev=SMBus(bus_no), address=address)
        return {
            "ok": True,
            "address": hex(address),
            "temperature": round(float(sensor.get_temperature()), 1),
            "humidity": round(float(sensor.get_humidity()), 1),
            "pressure": round(float(sensor.get_pressure()), 1),
        }
    except Exception as e:
        return {"ok": False, "message": str(e)}

def read_wind():
    return {"ok": True, "wind_mps": 0.0, "message": "待機中"}

@app.route("/")
def index():
    s = settings()
    return render_template("index.html", version=s.get("version", "2.0"), site_name=s.get("site_name", "星の館 全天カメラ"))

@app.route("/api/status")
def api_status():
    return jsonify({
        "ok": True,
        "version": settings().get("version", "2.0"),
        "time": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "latest_image": latest_file(IMG, ".jpg"),
        "latest_video": latest_file(VID, ".mp4"),
        "bme280": read_bme280(),
        "wind": read_wind(),
        "cloud": 33,
        "moon_age": moon_age(),
        "sqm": 20.8,
    })

@app.route("/api/capture", methods=["POST"])
def capture():
    s = settings()
    name = f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    out = IMG / name
    command = s["camera"]["capture_command"].format(output=str(out))
    try:
        r = cmd(command, timeout=30)
        if r.returncode != 0 or not out.exists():
            return jsonify({"ok": False, "message": (r.stderr or r.stdout or "capture failed")[-800:]})
        return jsonify({"ok": True, "filename": name, "message": f"保存しました: {name}"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})

@app.route("/api/video", methods=["POST"])
def video():
    s = settings()
    name_h264 = f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h264"
    out_h264 = VID / name_h264
    command = s["camera"]["video_command"].format(output=str(out_h264))
    try:
        r = cmd(command, timeout=40)
        if r.returncode != 0 or not out_h264.exists():
            return jsonify({"ok": False, "message": (r.stderr or r.stdout or "video failed")[-800:]})
        name_mp4 = name_h264.replace(".h264", ".mp4")
        out_mp4 = VID / name_mp4
        cmd(f"ffmpeg -y -i {out_h264} -c copy {out_mp4}", timeout=60)
        if out_mp4.exists():
            return jsonify({"ok": True, "filename": name_mp4, "message": f"動画保存: {name_mp4}"})
        return jsonify({"ok": True, "filename": name_h264, "message": f"動画保存: {name_h264}"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})

@app.route("/images/<path:filename>")
def images(filename):
    return send_from_directory(IMG, filename)

@app.route("/videos/<path:filename>")
def videos(filename):
    return send_from_directory(VID, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
