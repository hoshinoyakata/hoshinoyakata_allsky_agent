
from __future__ import annotations
from flask import Flask, jsonify, render_template, send_from_directory
from pathlib import Path
from datetime import datetime, timezone
import json, shutil, subprocess

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
IMG = DATA / "images"
VID = DATA / "videos"
CONFIG = BASE / "config" / "settings.json"
for p in (IMG, VID, DATA / "logs"):
    p.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, template_folder="templates", static_folder="static")

def settings():
    return json.loads(CONFIG.read_text(encoding="utf-8"))

def has_cmd(name):
    return shutil.which(name) is not None

def run(command, timeout=40):
    return subprocess.run(command, shell=True, text=True, capture_output=True, timeout=timeout)

def cam_still(out):
    c = settings()["camera"]; w=c.get("width",1920); h=c.get("height",1080); t=c.get("photo_timeout_ms",1000)
    if has_cmd("rpicam-still"):
        return f"rpicam-still -n --width {w} --height {h} --timeout {t} -o {out}"
    if has_cmd("libcamera-still"):
        return f"libcamera-still -n --width {w} --height {h} --timeout {t} -o {out}"
    return ""

def cam_vid(out):
    c = settings()["camera"]; w=c.get("width",1920); h=c.get("height",1080); t=c.get("video_time_ms",10000)
    if has_cmd("rpicam-vid"):
        return f"rpicam-vid -n -t {t} --width {w} --height {h} -o {out}"
    if has_cmd("libcamera-vid"):
        return f"libcamera-vid -n -t {t} --width {w} --height {h} -o {out}"
    return ""

def latest(folder, suffix):
    fs = sorted(folder.glob("*"+suffix), key=lambda p:p.stat().st_mtime, reverse=True)
    return fs[0].name if fs else None

def moon_age():
    epoch = datetime(2000,1,6,18,14,tzinfo=timezone.utc)
    return round(((datetime.now(timezone.utc)-epoch).total_seconds()/86400)%29.53058867,1)

def read_bme280():
    cfg=settings().get("bme280",{})
    try:
        from smbus2 import SMBus
        from bme280 import BME280
        addr = int(cfg.get("address","0x76"),16)
        sensor = BME280(i2c_dev=SMBus(int(cfg.get("bus",1))), address=addr)
        return {"ok":True,"address":hex(addr),"temperature":round(float(sensor.get_temperature()),1),
                "humidity":round(float(sensor.get_humidity()),1),"pressure":round(float(sensor.get_pressure()),1)}
    except Exception as e:
        return {"ok":False,"message":str(e)}

@app.route("/")
def index():
    s=settings()
    return render_template("index.html", site_name=s["site_name"], version=s["version"])

@app.route("/api/status")
def status():
    return jsonify({"ok":True,"version":settings()["version"],"latest_image":latest(IMG,".jpg"),
        "latest_video":latest(VID,".mp4"),"bme280":read_bme280(),"cloud":33,"moon_age":moon_age(),"sqm":20.8,
        "wind":{"ok":True,"wind_mps":0.0},
        "camera":{"rpicam_still":has_cmd("rpicam-still"),"rpicam_vid":has_cmd("rpicam-vid"),
                  "libcamera_still":has_cmd("libcamera-still"),"libcamera_vid":has_cmd("libcamera-vid")}})

@app.route("/api/capture", methods=["POST"])
def capture():
    name=f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"; out=IMG/name
    command=cam_still(out)
    if not command: return jsonify({"ok":False,"message":"rpicam-still / libcamera-still が見つかりません"})
    r=run(command)
    if r.returncode!=0 or not out.exists(): return jsonify({"ok":False,"message":(r.stderr or r.stdout or "capture failed")[-900:]})
    return jsonify({"ok":True,"filename":name,"message":f"保存しました: {name}"})

@app.route("/api/video", methods=["POST"])
def video():
    raw_name=f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h264"; raw=VID/raw_name
    command=cam_vid(raw)
    if not command: return jsonify({"ok":False,"message":"rpicam-vid / libcamera-vid が見つかりません"})
    r=run(command,60)
    if r.returncode!=0 or not raw.exists(): return jsonify({"ok":False,"message":(r.stderr or r.stdout or "video failed")[-900:]})
    mp4=VID/raw_name.replace(".h264",".mp4")
    if has_cmd("ffmpeg"): run(f"ffmpeg -y -i {raw} -c copy {mp4}",60)
    if mp4.exists(): return jsonify({"ok":True,"filename":mp4.name,"message":f"MP4保存しました: {mp4.name}"})
    return jsonify({"ok":True,"filename":raw.name,"message":f"H264保存しました: {raw.name}"})

@app.route("/images/<path:f>")
def images(f): return send_from_directory(IMG,f)
@app.route("/videos/<path:f>")
def videos(f): return send_from_directory(VID,f)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000)
