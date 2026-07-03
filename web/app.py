
from flask import Flask, jsonify, render_template, send_from_directory, request
from pathlib import Path
from datetime import datetime, timezone
import json, shutil, subprocess, platform, colorsys, statistics, time, math

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

def save_cfg(s):
    CONFIG.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")

def has_cmd(cmd):
    return shutil.which(cmd) is not None

def run(cmd, timeout=90):
    return subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)

def log(msg):
    with (LOG / "system.log").open("a", encoding="utf-8") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "  " + msg + "\n")

def latest(folder, suffix):
    fs = sorted(folder.glob("*" + suffix), key=lambda p: p.stat().st_mtime, reverse=True)
    return fs[0].name if fs else None

def latest_path():
    name = latest(IMG, ".jpg")
    return IMG / name if name else None

def recent_images(limit=5):
    fs = sorted(IMG.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [p.name for p in fs[:limit]]

def moon_age():
    epoch = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
    return round(((datetime.now(timezone.utc) - epoch).total_seconds() / 86400) % 29.53058867, 1)

def is_night_now():
    h = datetime.now().hour
    return h >= 18 or h <= 5

def camera_tool(prefix):
    if has_cmd("rpicam-" + prefix): return "rpicam-" + prefix
    if has_cmd("libcamera-" + prefix): return "libcamera-" + prefix
    return ""

def camera_still_command(out):
    s = cfg()
    c = s["camera"]
    w, h = c.get("width", 3072), c.get("height", 3072)
    mode = c.get("night_mode", "auto")
    night = is_night_now() if mode == "auto" else mode in ("night","low","medium","high","extreme")
    tool = camera_tool("still")
    if not tool: return ""
    if mode == "day" or not night:
        return f"{tool} -n --width {w} --height {h} --timeout {c.get('photo_timeout_ms_day',1000)} -o '{out}'"
    presets = {
        "low": {"exposure": 500000, "gain": 8, "timeout": 1000},
        "medium": {"exposure": 1000000, "gain": 14, "timeout": 1500},
        "high": {"exposure": 1800000, "gain": 20, "timeout": 2500},
        "extreme": {"exposure": 3000000, "gain": 26, "timeout": 3500},
        "auto": {"exposure": c.get("night_exposure_us",1800000), "gain": c.get("night_gain",20), "timeout": c.get("photo_timeout_ms_night",2500)},
        "night": {"exposure": c.get("night_exposure_us",1800000), "gain": c.get("night_gain",20), "timeout": c.get("photo_timeout_ms_night",2500)}
    }
    p = presets.get(mode, presets["auto"])
    return f"{tool} -n --width {w} --height {h} --shutter {int(p['exposure'])} --gain {float(p['gain'])} --awbgains 1.35,1.55 --denoise cdn_hq --timeout {int(p['timeout'])} -o '{out}'"

def camera_video_command(out):
    tool = camera_tool("vid")
    if not tool: return ""
    return f"{tool} -n -t {cfg()['camera'].get('video_time_ms',10000)} --width 1920 --height 1080 -o '{out}'"

def process_night_image(path):
    s = cfg().get("night_processing", {})
    if not s.get("enabled", True): return None
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        img = Image.open(path).convert("RGB")
        w,h = img.size
        px = img.load()
        sample = []
        step = max(1, min(w,h)//300)
        for y in range(0,h,step):
            for x in range(0,w,step):
                r,g,b = px[x,y]
                m = max(r,g,b)
                if 8 < m < 235: sample.append((r,g,b))
        green_excess = 0
        if sample:
            med_r = statistics.median([p[0] for p in sample])
            med_g = statistics.median([p[1] for p in sample])
            med_b = statistics.median([p[2] for p in sample])
            green_excess = max(0, med_g - ((med_r+med_b)/2))
        out = Image.new("RGB",(w,h))
        opx = out.load()
        cx,cy=w/2,h/2
        radius = min(w,h)*0.48
        for y in range(h):
            for x in range(w):
                r,g,b=px[x,y]
                d=((x-cx)**2+(y-cy)**2)**0.5
                if d < radius:
                    local_green = max(0, g-max(r,b))
                    if local_green > 10:
                        reduce = min(local_green*0.55 + green_excess*0.6, 55)
                        g = int(max(0, g-reduce))
                        b = int(min(255, b+reduce*0.10))
                        r = int(min(255, r+reduce*0.06))
                    if g > 165 and g > r*1.35 and g > b*1.15:
                        g=int(g*0.55); r=int(r*0.75); b=int(b*0.85)
                opx[x,y]=(r,g,b)
        out = out.filter(ImageFilter.MedianFilter(size=3))
        out = ImageEnhance.Contrast(out).enhance(1.12)
        out = ImageEnhance.Sharpness(out).enhance(1.08)
        processed = path.with_name(path.stem + "_nightai.jpg")
        out.save(processed, quality=92)
        return processed
    except Exception as e:
        log("夜間画像処理エラー: " + str(e))
        return None

def estimate_cloud_percent(image_path, night_active=False):
    try:
        from PIL import Image
        img = Image.open(image_path).convert("RGB")
        img.thumbnail((720,720))
        w,h=img.size
        px=img.load()
        cx,cy=w/2,h/2
        rlim=min(w,h)*0.42

        if night_active:
            # 夜は「星の数」と「空の明るさムラ」で雲量推定。
            # 星がほとんど見えず、全体がぼんやり明るい場合は曇り寄り。
            valid=stars=bright_haze=0
            for y in range(1,h-1):
                for x in range(1,w-1):
                    if ((x-cx)**2+(y-cy)**2)**0.5 > rlim: continue
                    R,G,B=px[x,y]; mx=max(R,G,B); mn=min(R,G,B)
                    if mx < 8: continue
                    valid += 1
                    # 点状の星っぽいもの
                    neigh = []
                    for yy in (y-1,y,y+1):
                        for xx in (x-1,x,x+1):
                            rr,gg,bb=px[xx,yy]
                            neigh.append(max(rr,gg,bb))
                    if mx > 110 and mx > (sum(neigh)/len(neigh) + 28) and (mx-mn) < 95:
                        stars += 1
                    # 雲・薄雲でぼんやり明るい領域
                    if 28 < mx < 170 and (mx-mn) < 80:
                        bright_haze += 1
            if valid < 500:
                return {"percent": 50, "message": "夜間雲量: 画像不足"}
            star_ratio = stars / valid
            haze_ratio = bright_haze / valid

            if star_ratio < 0.00008 and haze_ratio > 0.22:
                pct = 85
            elif star_ratio < 0.00015 and haze_ratio > 0.12:
                pct = 70
            elif star_ratio < 0.00035:
                pct = 55
            else:
                pct = max(0, min(100, int(45 - star_ratio*80000 + haze_ratio*45)))
            return {"percent": int(pct), "message": f"夜間AI解析 stars={stars}"}

        valid=sky=cloud=unknown=0
        for y in range(h):
            for x in range(w):
                if ((x-cx)**2+(y-cy)**2)**0.5 > rlim: continue
                R,G,B=px[x,y]; mx=max(R,G,B); mn=min(R,G,B)
                if mx<35: continue
                if mx>245 and (mx-mn)<18: continue
                valid+=1
                h0,s0,v0=colorsys.rgb_to_hsv(R/255,G/255,B/255)
                hue,sat,val=h0*360,s0*100,v0*100
                blue=(175<=hue<=245 and sat>=18 and val>=28 and B>=R+8)
                white=(sat<=34 and val>=45 and mx-mn<=70)
                gray=(sat<=28 and 28<=val<45)
                bright=(R>130 and G>130 and B>115 and sat<45)
                if blue: sky+=1
                elif white or gray or bright: cloud+=1
                else: unknown+=1
        if valid<500: return {"percent":33,"message":"雲量AI: 対象不足"}
        raw=(cloud+unknown*0.45)/valid*100
        if sky/valid<0.18 and raw<65: raw=max(raw,70)
        elif sky/valid<0.30 and raw<50: raw=max(raw,58)
        return {"percent":int(max(0,min(100,round(raw)))),"message":"昼間AI解析"}
    except Exception as e:
        return {"percent":33,"message":"雲量AIエラー: "+str(e)}

def read_wind():
    wc = cfg().get("wind", {})
    if not wc.get("enabled", True):
        return {"mps": 0, "direction": "--", "degrees": 0, "message": "風速 disabled"}
    pin = int(wc.get("gpio_pin", 17))
    seconds = float(wc.get("sample_seconds", 2.0))
    pulses_per_rotation = float(wc.get("pulses_per_rotation", 3))
    radius = float(wc.get("cup_radius_m", 0.04))
    factor = float(wc.get("calibration_factor", 1.0))
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        count = 0
        last = GPIO.input(pin)
        end = time.time() + seconds
        debounce = 0
        while time.time() < end:
            now = GPIO.input(pin)
            if last == 1 and now == 0 and time.time() - debounce > 0.02:
                count += 1
                debounce = time.time()
            last = now
            time.sleep(0.002)
        rps = (count / pulses_per_rotation) / seconds
        circumference = 2 * math.pi * radius
        mps = round(rps * circumference * factor, 1)
        return {"mps": mps, "direction": "未接続", "degrees": 0, "message": f"風速GPIO{pin}: {count} pulses/{seconds}s"}
    except Exception as e:
        return {"mps": 0, "direction": "未接続", "degrees": 0, "message": "風速未読込: " + str(e)[:80]}

def read_rain():
    rc = cfg().get("rain", {})
    if not rc.get("enabled", False):
        return {"label": "未接続", "message": "雨センサー未使用"}
    try:
        import RPi.GPIO as GPIO
        pin = int(rc.get("gpio_pin",27))
        active_low = bool(rc.get("active_low", True))
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        v = GPIO.input(pin)
        wet = (v == 0) if active_low else (v == 1)
        return {"label": "雨" if wet else "乾燥", "message": f"GPIO{pin}={'雨' if wet else '乾燥'}"}
    except Exception as e:
        return {"label": "未接続", "message": "雨センサー未読込: " + str(e)[:80]}

def detect_i2c(bus_no):
    found=[]
    try:
        from smbus2 import SMBus
        bus=SMBus(bus_no)
        for addr in range(3,120):
            try: bus.write_quick(addr); found.append(addr)
            except Exception: pass
        try: bus.close()
        except Exception: pass
    except Exception: pass
    return found

def read_bme280():
    bcfg=cfg().get("bme280",{})
    if not bcfg.get("enabled",True): return {"ok":False,"message":"BME280 disabled"}
    buses=[1,10,13,14] if bcfg.get("bus","auto")=="auto" else [int(bcfg["bus"])]
    addresses=[0x76,0x77] if bcfg.get("address","auto")=="auto" else [int(bcfg["address"],16) if isinstance(bcfg["address"],str) else int(bcfg["address"])]
    debug=[]
    try:
        from smbus2 import SMBus
        from bme280 import BME280
    except Exception as e:
        return {"ok":False,"message":"BME280ライブラリ読込失敗: "+str(e)}
    for bus_no in buses:
        visible=detect_i2c(bus_no)
        if visible: debug.append(f"bus {bus_no}: "+",".join(hex(x) for x in visible))
        for addr in addresses:
            try:
                dev=SMBus(bus_no)
                try: sensor=BME280(i2c_dev=dev, i2c_addr=addr)
                except TypeError:
                    sensor=BME280(i2c_dev=dev)
                    if hasattr(sensor,"i2c_addr"): sensor.i2c_addr=addr
                temp=round(float(sensor.get_temperature()),1)
                hum=round(float(sensor.get_humidity()),1)
                press=round(float(sensor.get_pressure()),1)
                try: dev.close()
                except Exception: pass
                return {"ok":True,"bus":bus_no,"address":hex(addr),"temperature":temp,"humidity":hum,"pressure":press,"message":f"BME280 正常 bus{bus_no} {hex(addr)}"}
            except Exception as e:
                debug.append(f"bus {bus_no} addr {hex(addr)} NG: {str(e)[:80]}")
    return {"ok":False,"message":"BME280を読めません: "+" / ".join(debug[-8:])}

def system_info():
    ip=run("hostname -I | awk '{print $1}'",5).stdout.strip()
    uptime=run("uptime -p",5).stdout.strip().replace("up ","")
    try:
        disk=shutil.disk_usage(str(BASE))
        storage=f"{round((disk.total-disk.free)/1024**3,1)}GB / {round(disk.total/1024**3,1)}GB"
    except Exception: storage="--"
    return {"ip":ip,"uptime":uptime,"storage":storage,"os":platform.platform(),"camera":"正常" if camera_tool("still") else "未確認"}

@app.route("/")
def index():
    s=cfg()
    return render_template("index.html", site_name=s["site_name"], version=s["version"])

@app.route("/api/status")
def status():
    s=cfg(); bme=read_bme280(); now=datetime.now()
    lp=latest_path()
    mode=s["camera"].get("night_mode","auto")
    night_active=is_night_now() if mode=="auto" else mode in ("night","low","medium","high","extreme")
    cloud=estimate_cloud_percent(lp, night_active=night_active) if lp and lp.exists() else {"percent":33,"message":"画像待機中"}
    c=s["camera"]
    return jsonify({"ok":True,"version":s["version"],"time":now.strftime("%H:%M:%S"),"date":now.strftime("%Y/%m/%d"),
        "latest_image":lp.name if lp else None,"recent_images":recent_images(),"bme280":bme,
        "cloud":cloud["percent"],"cloud_message":cloud["message"],"moon_age":round(moon_age()),"sqm":20.6,
        "wind":read_wind(),"rain":read_rain(),"system":system_info(),
        "night":{"mode":mode,"active":night_active,"exposure_us":c.get("night_exposure_us",1800000),"gain":c.get("night_gain",20)}})

@app.route("/api/night_mode", methods=["POST"])
def night_mode():
    data=request.get_json(force=True,silent=True) or {}
    mode=data.get("mode","auto")
    if mode not in ["auto","day","low","medium","high","extreme","night"]:
        return jsonify({"ok":False,"message":"modeが不正です"})
    s=cfg(); s["camera"]["night_mode"]=mode; save_cfg(s)
    return jsonify({"ok":True,"message":f"星空感度: {mode}"})

@app.route("/api/capture", methods=["POST"])
def capture():
    name=f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    out=IMG/name
    cmd=camera_still_command(out)
    if not cmd: return jsonify({"ok":False,"message":"rpicam-still / libcamera-still が見つかりません"})
    r=run(cmd,120)
    if r.returncode!=0 or not out.exists(): return jsonify({"ok":False,"message":(r.stderr or r.stdout or "撮影失敗")[-1200:]})
    final=out
    if is_night_now() or cfg()["camera"].get("night_mode") in ("low","medium","high","extreme","night"):
        processed=process_night_image(out)
        if processed: final=processed
    return jsonify({"ok":True,"filename":final.name,"message":f"保存しました: {final.name}"})

@app.route("/api/video", methods=["POST"])
def video():
    raw=VID/f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h264"
    cmd=camera_video_command(raw)
    if not cmd: return jsonify({"ok":False,"message":"rpicam-vid / libcamera-vid が見つかりません"})
    r=run(cmd,80)
    if r.returncode!=0 or not raw.exists(): return jsonify({"ok":False,"message":(r.stderr or r.stdout or "録画失敗")[-1200:]})
    mp4=VID/(raw.stem+".mp4")
    if has_cmd("ffmpeg"): run(f"ffmpeg -y -i '{raw}' -c copy '{mp4}'",80)
    return jsonify({"ok":True,"filename":mp4.name if mp4.exists() else raw.name,"message":"動画を保存しました"})

@app.route("/images/<path:name>")
def images(name):
    return send_from_directory(IMG,name)
@app.route("/videos/<path:name>")
def videos(name):
    return send_from_directory(VID,name)
if __name__=="__main__":
    log("システム起動")
    app.run(host="0.0.0.0", port=5000)
