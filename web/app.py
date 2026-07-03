
from flask import Flask, jsonify, render_template, send_from_directory
from pathlib import Path
from datetime import datetime, timezone
import json, shutil, subprocess, platform

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
IMG = DATA / "images"
VID = DATA / "videos"
LOG = DATA / "logs"
CONFIG = BASE / "config" / "settings.json"

for p in (IMG, VID, LOG):
    p.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, template_folder="templates", static_folder="static")

def cfg():
    return json.loads(CONFIG.read_text(encoding="utf-8"))

def has_cmd(cmd):
    return shutil.which(cmd) is not None

def run(cmd, timeout=40):
    return subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)

def log(msg):
    with (LOG / "system.log").open("a", encoding="utf-8") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "  " + msg + "\n")

def latest(folder, suffix):
    fs = sorted(folder.glob("*" + suffix), key=lambda p: p.stat().st_mtime, reverse=True)
    return fs[0].name if fs else None

def recent_images(limit=5):
    fs = sorted(IMG.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [p.name for p in fs[:limit]]

def moon_age():
    epoch = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
    return round(((datetime.now(timezone.utc) - epoch).total_seconds() / 86400) % 29.53058867, 1)

def camera_still_command(out):
    c = cfg()["camera"]
    w = c.get("width", 3072)
    h = c.get("height", 3072)
    t = c.get("photo_timeout_ms", 1000)

    # 正方形指定。カメラ側が対応しない場合でも rpicam が近いモードに合わせます。
    if has_cmd("rpicam-still"):
        return f"rpicam-still -n --width {w} --height {h} --timeout {t} -o '{out}'"
    if has_cmd("libcamera-still"):
        return f"libcamera-still -n --width {w} --height {h} --timeout {t} -o '{out}'"
    return ""

def camera_video_command(out):
    c = cfg()["camera"]
    t = c.get("video_time_ms", 10000)
    # 動画は互換性重視で 1920x1080
    if has_cmd("rpicam-vid"):
        return f"rpicam-vid -n -t {t} --width 1920 --height 1080 -o '{out}'"
    if has_cmd("libcamera-vid"):
        return f"libcamera-vid -n -t {t} --width 1920 --height 1080 -o '{out}'"
    return ""

def detect_i2c(bus_no):
    found = []
    try:
        from smbus2 import SMBus
        bus = SMBus(bus_no)
        for addr in range(3, 120):
            try:
                bus.write_quick(addr)
                found.append(addr)
            except Exception:
                pass
        try:
            bus.close()
        except Exception:
            pass
    except Exception:
        pass
    return found

def read_bme280():
    bcfg = cfg().get("bme280", {})
    if not bcfg.get("enabled", True):
        return {"ok": False, "message": "BME280 disabled"}

    buses = [1, 10, 13, 14] if bcfg.get("bus", "auto") == "auto" else [int(bcfg["bus"])]
    addresses = [0x76, 0x77] if bcfg.get("address", "auto") == "auto" else [int(bcfg["address"], 16) if isinstance(bcfg["address"], str) else int(bcfg["address"])]
    debug = []

    try:
        from smbus2 import SMBus
        from bme280 import BME280
    except Exception as e:
        return {"ok": False, "message": "BME280ライブラリ読込失敗: " + str(e)}

    for bus_no in buses:
        visible = detect_i2c(bus_no)
        if visible:
            debug.append(f"bus {bus_no}: " + ",".join(hex(x) for x in visible))

        for addr in addresses:
            try:
                dev = SMBus(bus_no)
                try:
                    sensor = BME280(i2c_dev=dev, i2c_addr=addr)
                except TypeError:
                    sensor = BME280(i2c_dev=dev)
                    if hasattr(sensor, "i2c_addr"):
                        sensor.i2c_addr = addr

                temp = round(float(sensor.get_temperature()), 1)
                hum = round(float(sensor.get_humidity()), 1)
                press = round(float(sensor.get_pressure()), 1)

                try:
                    dev.close()
                except Exception:
                    pass

                return {
                    "ok": True,
                    "bus": bus_no,
                    "address": hex(addr),
                    "temperature": temp,
                    "humidity": hum,
                    "pressure": press,
                    "message": f"BME280 正常 bus{bus_no} {hex(addr)}"
                }
            except Exception as e:
                debug.append(f"bus {bus_no} addr {hex(addr)} NG: {str(e)[:80]}")

    return {"ok": False, "message": "BME280を読めません: " + " / ".join(debug[-8:])}

def system_info():
    ip = run("hostname -I | awk '{print $1}'", 5).stdout.strip()
    uptime = run("uptime -p", 5).stdout.strip().replace("up ", "")
    try:
        disk = shutil.disk_usage(str(BASE))
        storage = f"{round((disk.total-disk.free)/1024**3,1)}GB / {round(disk.total/1024**3,1)}GB"
    except Exception:
        storage = "--"
    return {
        "ip": ip,
        "uptime": uptime,
        "storage": storage,
        "os": platform.platform(),
        "camera": "正常" if has_cmd("rpicam-still") or has_cmd("libcamera-still") else "未確認"
    }

@app.route("/")
def index():
    s = cfg()
    return render_template("index.html", site_name=s["site_name"], version=s["version"])

@app.route("/api/status")
def status():
    bme = read_bme280()
    s = cfg()
    now = datetime.now()
    return jsonify({
        "ok": True,
        "version": s["version"],
        "time": now.strftime("%H:%M:%S"),
        "date": now.strftime("%Y/%m/%d"),
        "latest_image": latest(IMG, ".jpg"),
        "recent_images": recent_images(),
        "bme280": bme,
        "cloud": 28 if bme.get("ok") else 33,
        "moon_age": round(moon_age()),
        "sqm": 20.6,
        "wind": {"mps": 1.2, "direction": "西北西", "degrees": 292},
        "rain": {"label": "乾燥", "message": "雨なし"},
        "system": system_info(),
        "ai": {
            "meteor": "待機中",
            "fireball": "待機中",
            "cloud": "待機中",
            "aurora": "待機中",
            "thunder": "待機中",
            "iss": "待機中"
        }
    })

@app.route("/api/capture", methods=["POST"])
def capture():
    name = f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    out = IMG / name
    cmd = camera_still_command(out)
    if not cmd:
        return jsonify({"ok": False, "message": "rpicam-still / libcamera-still が見つかりません"})

    r = run(cmd, 60)
    if r.returncode != 0 or not out.exists():
        return jsonify({"ok": False, "message": (r.stderr or r.stdout or "撮影失敗")[-1200:]})

    log(f"撮影しました: {name}")
    return jsonify({"ok": True, "filename": name, "message": f"保存しました: {name}"})

@app.route("/api/video", methods=["POST"])
def video():
    raw = VID / f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h264"
    cmd = camera_video_command(raw)
    if not cmd:
        return jsonify({"ok": False, "message": "rpicam-vid / libcamera-vid が見つかりません"})

    r = run(cmd, 80)
    if r.returncode != 0 or not raw.exists():
        return jsonify({"ok": False, "message": (r.stderr or r.stdout or "録画失敗")[-1200:]})

    mp4 = VID / (raw.stem + ".mp4")
    if has_cmd("ffmpeg"):
        run(f"ffmpeg -y -i '{raw}' -c copy '{mp4}'", 80)

    log(f"動画保存: {mp4.name if mp4.exists() else raw.name}")
    return jsonify({"ok": True, "filename": mp4.name if mp4.exists() else raw.name, "message": "動画を保存しました"})

@app.route("/images/<path:name>")
def images(name):
    return send_from_directory(IMG, name)

@app.route("/videos/<path:name>")
def videos(name):
    return send_from_directory(VID, name)

if __name__ == "__main__":
    log("システム起動")
    app.run(host="0.0.0.0", port=5000)
