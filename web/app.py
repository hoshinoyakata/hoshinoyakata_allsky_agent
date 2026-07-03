from flask import Flask, jsonify, render_template, send_from_directory, request
from pathlib import Path
from datetime import datetime, timezone
import json, shutil, subprocess, platform, colorsys

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
IMG = DATA / "images"
VID = DATA / "videos"
LOG = DATA / "logs"
CONFIG = BASE / "config" / "settings.json"
for p in (IMG, VID, LOG): p.mkdir(parents=True, exist_ok=True)
app = Flask(__name__, template_folder="templates", static_folder="static")

def cfg(): return json.loads(CONFIG.read_text(encoding="utf-8"))
def save_cfg(s): CONFIG.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
def has_cmd(cmd): return shutil.which(cmd) is not None
def run(cmd, timeout=90): return subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)
def log(msg):
    with (LOG/"system.log").open("a", encoding="utf-8") as f: f.write(datetime.now().strftime("%F %T  ")+msg+"\n")
def latest(folder, suffix):
    fs=sorted(folder.glob("*"+suffix), key=lambda p:p.stat().st_mtime, reverse=True)
    return fs[0].name if fs else None
def latest_path():
    n=latest(IMG,".jpg"); return IMG/n if n else None
def recent_images(limit=5): return [p.name for p in sorted(IMG.glob("*.jpg"), key=lambda p:p.stat().st_mtime, reverse=True)[:limit]]
def moon_age():
    epoch=datetime(2000,1,6,18,14,tzinfo=timezone.utc)
    return round(((datetime.now(timezone.utc)-epoch).total_seconds()/86400)%29.53058867,1)
def is_night_now():
    h=datetime.now().hour; return h>=18 or h<=5
def camera_tool(kind):
    if has_cmd("rpicam-"+kind): return "rpicam-"+kind
    if has_cmd("libcamera-"+kind): return "libcamera-"+kind
    return ""

def camera_still_command(out):
    s=cfg(); c=s["camera"]; w=c.get("width",3072); h=c.get("height",3072)
    mode=c.get("night_mode","auto"); night = is_night_now() if mode=="auto" else mode in ["night","low","medium","high","extreme"]
    tool=camera_tool("still")
    if not tool: return ""
    if not night:
        return f"{tool} -n --width {w} --height {h} --timeout {c.get('photo_timeout_ms_day',1000)} -o '{out}'"
    presets={
      "low":(500000,12,1000), "medium":(1000000,18,1500), "high":(1500000,24,2000), "extreme":(2500000,32,3000),
      "auto":(c.get("night_exposure_us",1500000),c.get("night_gain",24),c.get("photo_timeout_ms_night",2000)),
      "night":(c.get("night_exposure_us",1500000),c.get("night_gain",24),c.get("photo_timeout_ms_night",2000))}
    exp,gain,t=presets.get(mode,presets["auto"])
    return f"{tool} -n --width {w} --height {h} --shutter {int(exp)} --gain {float(gain)} --awbgains 1.5,1.5 --denoise cdn_hq --timeout {int(t)} -o '{out}'"

def camera_video_command(out):
    tool=camera_tool("vid")
    return f"{tool} -n -t 10000 --width 1920 --height 1080 -o '{out}'" if tool else ""

def estimate_cloud_percent(path):
    if not path or not path.exists(): return {"percent":33,"message":"画像待機中"}
    if is_night_now(): return {"percent":0,"message":"夜間のため雲量参考値"}
    try:
        from PIL import Image
        img=Image.open(path).convert("RGB"); img.thumbnail((720,720)); w,h=img.size; px=img.load(); cx,cy=w/2,h/2; r=min(w,h)*0.42
        valid=sky=cloud=unknown=0
        for y in range(h):
            for x in range(w):
                if ((x-cx)**2+(y-cy)**2)**0.5>r: continue
                R,G,B=px[x,y]; mx=max(R,G,B); mn=min(R,G,B)
                if mx<35 or (mx>245 and mx-mn<18): continue
                valid+=1; hue,sat,val=colorsys.rgb_to_hsv(R/255,G/255,B/255); hue*=360; sat*=100; val*=100
                blue=(175<=hue<=245 and sat>=18 and val>=28 and B>=R+8)
                white=(sat<=34 and val>=45 and mx-mn<=70)
                gray=(sat<=28 and 28<=val<45)
                bright=(R>130 and G>130 and B>115 and sat<45)
                if blue: sky+=1
                elif white or gray or bright: cloud+=1
                else: unknown+=1
        if valid<500: return {"percent":33,"message":"雲量AI: 対象不足"}
        raw=(cloud+unknown*0.45)/valid*100; sky_ratio=sky/valid
        if sky_ratio<0.18 and raw<65: raw=max(raw,70)
        elif sky_ratio<0.30 and raw<50: raw=max(raw,58)
        return {"percent":int(max(0,min(100,round(raw)))),"message":"画像AI解析"}
    except Exception as e: return {"percent":33,"message":"雲量AIエラー"}

def read_bme280():
    try:
        from smbus2 import SMBus
        from bme280 import BME280
        for bus_no in [1,10,13,14]:
            for addr in [0x76,0x77]:
                try:
                    dev=SMBus(bus_no)
                    try: sensor=BME280(i2c_dev=dev, i2c_addr=addr)
                    except TypeError: sensor=BME280(i2c_dev=dev)
                    temp=round(float(sensor.get_temperature()),1); hum=round(float(sensor.get_humidity()),1); press=round(float(sensor.get_pressure()),1)
                    try: dev.close()
                    except Exception: pass
                    return {"ok":True,"temperature":temp,"humidity":hum,"pressure":press,"message":f"BME280 正常 bus{bus_no} {hex(addr)}"}
                except Exception: pass
    except Exception as e: return {"ok":False,"message":"BME280ライブラリ読込失敗: "+str(e)}
    return {"ok":False,"message":"BME280を読めません"}

def system_info():
    ip=run("hostname -I | awk '{print $1}'",5).stdout.strip(); uptime=run("uptime -p",5).stdout.strip().replace("up ","")
    return {"ip":ip,"uptime":uptime,"camera":"正常" if camera_tool("still") else "未確認","os":platform.platform()}

@app.route("/")
def index():
    s=cfg(); return render_template("index.html", site_name=s["site_name"], version=s["version"])
@app.route("/api/status")
def status():
    s=cfg(); bme=read_bme280(); lp=latest_path(); cloud=estimate_cloud_percent(lp); c=s["camera"]; mode=c.get("night_mode","auto")
    active=is_night_now() if mode=="auto" else mode in ["night","low","medium","high","extreme"]
    return jsonify({"ok":True,"version":s["version"],"time":datetime.now().strftime("%H:%M:%S"),"date":datetime.now().strftime("%Y/%m/%d"),"latest_image":lp.name if lp else None,"recent_images":recent_images(),"bme280":bme,"cloud":cloud["percent"],"cloud_message":cloud["message"],"moon_age":round(moon_age()),"sqm":20.6,"wind":{"mps":1.2,"direction":"西北西","degrees":292},"rain":{"label":"乾燥"},"system":system_info(),"night":{"mode":mode,"active":active,"exposure_us":c.get("night_exposure_us",1500000),"gain":c.get("night_gain",24)}})
@app.route("/api/night_mode", methods=["POST"])
def night_mode():
    data=request.get_json(force=True, silent=True) or {}; mode=data.get("mode","auto")
    if mode not in ["auto","day","low","medium","high","extreme","night"]: return jsonify({"ok":False,"message":"mode不正"})
    s=cfg(); s["camera"]["night_mode"]=mode; save_cfg(s); log("夜間モード変更: "+mode); return jsonify({"ok":True,"message":"星空感度: "+mode.upper()})
@app.route("/api/capture", methods=["POST"])
def capture():
    name=f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"; out=IMG/name; cmd=camera_still_command(out)
    if not cmd: return jsonify({"ok":False,"message":"rpicam-still / libcamera-still が見つかりません"})
    r=run(cmd,90)
    if r.returncode!=0 or not out.exists(): return jsonify({"ok":False,"message":(r.stderr or r.stdout or "撮影失敗")[-1200:]})
    return jsonify({"ok":True,"filename":name,"message":"保存しました: "+name})
@app.route("/api/video", methods=["POST"])
def video():
    raw=VID/f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h264"; cmd=camera_video_command(raw)
    if not cmd: return jsonify({"ok":False,"message":"rpicam-vid / libcamera-vid が見つかりません"})
    r=run(cmd,80)
    return jsonify({"ok":r.returncode==0,"filename":raw.name,"message":"動画を保存しました" if r.returncode==0 else (r.stderr or "録画失敗")[-1200:]})
@app.route("/images/<path:name>")
def images(name): return send_from_directory(IMG,name)
@app.route("/videos/<path:name>")
def videos(name): return send_from_directory(VID,name)
if __name__=="__main__": app.run(host="0.0.0.0", port=5000)
