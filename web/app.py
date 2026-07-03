
from flask import Flask, jsonify, render_template, send_from_directory
from pathlib import Path
from datetime import datetime, timezone
import json, shutil, subprocess, platform

BASE=Path(__file__).resolve().parents[1]
DATA=BASE/"data"; IMG=DATA/"images"; VID=DATA/"videos"; LOG=DATA/"logs"; CONFIG=BASE/"config/settings.json"
for p in (IMG,VID,LOG): p.mkdir(parents=True,exist_ok=True)
app=Flask(__name__, template_folder="templates", static_folder="static")

def cfg(): return json.loads(CONFIG.read_text(encoding="utf-8"))
def has(c): return shutil.which(c) is not None
def run(cmd,t=40): return subprocess.run(cmd,shell=True,text=True,capture_output=True,timeout=t)
def log(msg):
    with (LOG/"system.log").open("a",encoding="utf-8") as f: f.write(datetime.now().strftime("%H:%M:%S")+"  "+msg+"\n")
def logs(n=8):
    f=LOG/"system.log"
    return f.read_text(encoding="utf-8",errors="ignore").splitlines()[-n:] if f.exists() else ["システム起動待機中"]
def latest(folder,suffix):
    fs=sorted(folder.glob("*"+suffix), key=lambda p:p.stat().st_mtime, reverse=True)
    return fs[0].name if fs else None
def moon_age():
    e=datetime(2000,1,6,18,14,tzinfo=timezone.utc)
    return round(((datetime.now(timezone.utc)-e).total_seconds()/86400)%29.53058867,1)
def cam_still(out):
    c=cfg()["camera"]; w=c.get("width",1920); h=c.get("height",1080); tm=c.get("photo_timeout_ms",1000)
    if has("rpicam-still"): return f"rpicam-still -n --width {w} --height {h} --timeout {tm} -o '{out}'"
    if has("libcamera-still"): return f"libcamera-still -n --width {w} --height {h} --timeout {tm} -o '{out}'"
    return ""
def cam_vid(out):
    c=cfg()["camera"]; w=c.get("width",1920); h=c.get("height",1080); tm=c.get("video_time_ms",10000)
    if has("rpicam-vid"): return f"rpicam-vid -n -t {tm} --width {w} --height {h} -o '{out}'"
    if has("libcamera-vid"): return f"libcamera-vid -n -t {tm} --width {w} --height {h} -o '{out}'"
    return ""
def detect(bus_no):
    found=[]
    try:
        from smbus2 import SMBus
        b=SMBus(bus_no)
        for a in range(3,120):
            try: b.write_quick(a); found.append(a)
            except Exception: pass
        try: b.close()
        except Exception: pass
    except Exception: pass
    return found
def read_bme():
    bcfg=cfg().get("bme280",{})
    if not bcfg.get("enabled",True): return {"ok":False,"message":"BME280 disabled"}
    buses=[1,10,13,14] if bcfg.get("bus","auto")=="auto" else [int(bcfg["bus"])]
    addrs=[0x76,0x77] if bcfg.get("address","auto")=="auto" else [int(bcfg["address"],16) if isinstance(bcfg["address"],str) else int(bcfg["address"])]
    dbg=[]
    try:
        from smbus2 import SMBus
        from bme280 import BME280
    except Exception as e:
        return {"ok":False,"message":"BME280ライブラリ読込失敗: "+str(e)}
    for bus_no in buses:
        vis=detect(bus_no)
        if vis: dbg.append(f"bus {bus_no}: "+",".join(hex(x) for x in vis))
        for addr in addrs:
            try:
                dev=SMBus(bus_no)
                try:
                    sensor=BME280(i2c_dev=dev, i2c_addr=addr)
                except TypeError:
                    sensor=BME280(i2c_dev=dev)
                    if hasattr(sensor,"i2c_addr"): sensor.i2c_addr=addr
                t=round(float(sensor.get_temperature()),1)
                h=round(float(sensor.get_humidity()),1)
                p=round(float(sensor.get_pressure()),1)
                try: dev.close()
                except Exception: pass
                return {"ok":True,"bus":bus_no,"address":hex(addr),"temperature":t,"humidity":h,"pressure":p,"message":f"BME280 正常 bus{bus_no} {hex(addr)}"}
            except Exception as e:
                dbg.append(f"bus {bus_no} addr {hex(addr)} NG: {str(e)[:70]}")
    return {"ok":False,"message":"BME280を読めません: "+" / ".join(dbg[-8:])}
def sysinfo():
    ip=run("hostname -I | awk '{print $1}'",5).stdout.strip()
    try:
        du=shutil.disk_usage(str(BASE)); st=f"{round((du.total-du.free)/1024**3,1)}GB / {round(du.total/1024**3,1)}GB"
    except Exception: st="--"
    up=run("uptime -p",5).stdout.strip().replace("up ","")
    return {"device":"Raspberry Pi 5","os":platform.platform(),"ip":ip,"storage":st,"uptime":up}
def hist():
    return {"temp":[21.8,21.2,20.5,19.8,20.4,21.5],"hum":[64,66,70,73,71,69.8],"press":[713,713,712,711,712,712.9],"wind":[0,0.3,0,0.8,0.1,0],"sqm":[20.8,20.9,21,20.9,20.8,20.8],"cloud":[33,30,42,50,41,33]}
@app.route("/")
def index():
    s=cfg(); return render_template("index.html",site_name=s["site_name"],version=s["version"])
@app.route("/api/status")
def status():
    b=read_bme(); s=cfg()
    return jsonify({"ok":True,"version":s["version"],"now":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "latest_image":latest(IMG,".jpg"),"latest_video":latest(VID,".mp4") or latest(VID,".h264"),
    "bme280":b,"cloud":33,"cloud_label":"薄曇り","moon_age":moon_age(),"sqm":20.8,
    "wind":{"ok":True,"avg_mps":0.0,"wind_mps":0.0,"max_today":0.0},
    "rain":{"ok":True,"raining":False,"label":"晴れ","message":"降水なし"},
    "camera":{"rpicam_still":has("rpicam-still"),"rpicam_vid":has("rpicam-vid"),"status":"正常動作中"},
    "history":hist(),"logs":logs(),"system":sysinfo(),"schedule":s.get("schedule",{})})
@app.route("/api/capture",methods=["POST"])
def capture():
    name=f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"; out=IMG/name; cmd=cam_still(out)
    if not cmd: return jsonify({"ok":False,"message":"rpicam-still / libcamera-still が見つかりません"})
    r=run(cmd,45)
    if r.returncode!=0 or not out.exists(): return jsonify({"ok":False,"message":(r.stderr or r.stdout or "capture failed")[-1000:]})
    log("全天画像を更新しました"); return jsonify({"ok":True,"filename":name,"message":f"保存しました: {name}"})
@app.route("/api/video",methods=["POST"])
def video():
    raw=VID/f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h264"; cmd=cam_vid(raw)
    if not cmd: return jsonify({"ok":False,"message":"rpicam-vid / libcamera-vid が見つかりません"})
    r=run(cmd,70)
    if r.returncode!=0 or not raw.exists(): return jsonify({"ok":False,"message":(r.stderr or r.stdout or "video failed")[-1000:]})
    mp4=VID/(raw.stem+".mp4")
    if has("ffmpeg"): run(f"ffmpeg -y -i '{raw}' -c copy '{mp4}'",60)
    log("MP4動画を保存しました")
    return jsonify({"ok":True,"filename":mp4.name if mp4.exists() else raw.name,"message":"動画を保存しました"})
@app.route("/images/<path:f>")
def images(f): return send_from_directory(IMG,f)
@app.route("/videos/<path:f>")
def videos(f): return send_from_directory(VID,f)
if __name__=="__main__":
    log("システム起動"); app.run(host="0.0.0.0",port=5000)
