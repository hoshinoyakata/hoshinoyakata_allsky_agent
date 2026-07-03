
from flask import Flask,jsonify,render_template,send_from_directory,request
from pathlib import Path
from datetime import datetime,timezone
import json,shutil,subprocess,time,math,colorsys
BASE=Path(__file__).resolve().parents[1]; IMG=BASE/"data/images"; VID=BASE/"data/videos"; CONFIG=BASE/"config/settings.json"
IMG.mkdir(parents=True,exist_ok=True); VID.mkdir(parents=True,exist_ok=True)
app=Flask(__name__,template_folder="templates",static_folder="static")
def cfg(): return json.loads(CONFIG.read_text(encoding="utf-8"))
def save_cfg(s): CONFIG.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding="utf-8")
def has(c): return shutil.which(c) is not None
def run(c,t=90): return subprocess.run(c,shell=True,text=True,capture_output=True,timeout=t)
def camtool(k): return "rpicam-"+k if has("rpicam-"+k) else ("libcamera-"+k if has("libcamera-"+k) else "")
def night(): return datetime.now().hour>=18 or datetime.now().hour<=5
def latest_img():
    fs=sorted(IMG.glob("*.jpg"),key=lambda p:p.stat().st_mtime,reverse=True); return fs[0] if fs else None
def recent(n=5):
    return [p.name for p in sorted(IMG.glob("*.jpg"),key=lambda p:p.stat().st_mtime,reverse=True)[:n]]
def moon_age():
    e=datetime(2000,1,6,18,14,tzinfo=timezone.utc); return round(((datetime.now(timezone.utc)-e).total_seconds()/86400)%29.53058867,1)
def still_cmd(out):
    s=cfg(); c=s["camera"]; tool=camtool("still")
    if not tool: return ""
    mode=c.get("night_mode","auto"); active=night() if mode=="auto" else mode in ["low","medium","high","extreme","night"]
    w,h=c.get("width",3072),c.get("height",3072)
    if mode=="day" or not active:
        return f"{tool} -n --width {w} --height {h} --timeout {c.get('photo_timeout_ms_day',1000)} -o '{out}'"
    presets={"low":(500000,8,1000),"medium":(1000000,14,1500),"high":(1800000,20,2500),"extreme":(3000000,26,3500),"auto":(c.get("night_exposure_us",1800000),c.get("night_gain",20),c.get("photo_timeout_ms_night",2500)),"night":(c.get("night_exposure_us",1800000),c.get("night_gain",20),c.get("photo_timeout_ms_night",2500))}
    ex,g,t=presets.get(mode,presets["auto"])
    return f"{tool} -n --width {w} --height {h} --shutter {ex} --gain {g} --awbgains 1.35,1.55 --denoise cdn_hq --timeout {t} -o '{out}'"
def cloud(p,active=False):
    if not p or not p.exists(): return 33,"画像待機中"
    try:
        from PIL import Image
        im=Image.open(p).convert("RGB"); im.thumbnail((640,640)); w,h=im.size; px=im.load(); cx,cy=w/2,h/2; r=min(w,h)*.42
        if active:
            valid=stars=haze=0
            for y in range(1,h-1,2):
              for x in range(1,w-1,2):
                if ((x-cx)**2+(y-cy)**2)**.5>r: continue
                R,G,B=px[x,y]; mx=max(R,G,B); mn=min(R,G,B)
                if mx<8: continue
                valid+=1
                ns=[max(px[xx,yy]) for yy in (y-1,y,y+1) for xx in (x-1,x,x+1)]
                if mx>105 and mx>sum(ns)/len(ns)+24 and mx-mn<95: stars+=1
                if 24<mx<175 and mx-mn<85: haze+=1
            if valid<300: return 50,"夜間雲量:画像不足"
            sr,hr=stars/valid,haze/valid
            if sr<.00008 and hr>.22: pct=85
            elif sr<.00015 and hr>.12: pct=70
            elif sr<.00035: pct=55
            else: pct=max(0,min(100,int(45-sr*80000+hr*45)))
            return pct,f"夜間AI stars={stars}"
        valid=sky=cld=unk=0
        for y in range(h):
          for x in range(w):
            if ((x-cx)**2+(y-cy)**2)**.5>r: continue
            R,G,B=px[x,y]; mx=max(R,G,B); mn=min(R,G,B)
            if mx<35 or (mx>245 and mx-mn<18): continue
            valid+=1; hh,ss,vv=colorsys.rgb_to_hsv(R/255,G/255,B/255); hue=hh*360; sat=ss*100; val=vv*100
            blue=175<=hue<=245 and sat>=18 and val>=28 and B>=R+8
            white=sat<=34 and val>=45 and mx-mn<=70
            gray=sat<=28 and 28<=val<45
            bright=R>130 and G>130 and B>115 and sat<45
            if blue: sky+=1
            elif white or gray or bright: cld+=1
            else: unk+=1
        if valid<500: return 33,"雲量AI:対象不足"
        raw=(cld+unk*.45)/valid*100
        if sky/valid<.18 and raw<65: raw=70
        elif sky/valid<.30 and raw<50: raw=58
        return int(max(0,min(100,round(raw)))),"画像AI解析"
    except Exception: return 33,"雲量AIエラー"
def read_bme():
    try:
        from smbus2 import SMBus
        from bme280 import BME280
        for busno in [1,10,13,14]:
            for addr in [0x76,0x77]:
                try:
                    dev=SMBus(busno)
                    try: sensor=BME280(i2c_dev=dev,i2c_addr=addr)
                    except TypeError: sensor=BME280(i2c_dev=dev)
                    return {"ok":True,"temperature":round(float(sensor.get_temperature()),1),"humidity":round(float(sensor.get_humidity()),1),"pressure":round(float(sensor.get_pressure()),1),"message":f"BME280 bus{busno} {hex(addr)}"}
                except Exception: pass
    except Exception: pass
    return {"ok":False,"message":"BME280未読込"}
def read_wind():
    w=cfg().get("wind",{}); pin=int(w.get("gpio_pin",17))
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM); GPIO.setup(pin,GPIO.IN,pull_up_down=GPIO.PUD_UP)
        count=0; last=GPIO.input(pin); end=time.time()+float(w.get("sample_seconds",2)); deb=0
        while time.time()<end:
            now=GPIO.input(pin)
            if last==1 and now==0 and time.time()-deb>.02: count+=1; deb=time.time()
            last=now; time.sleep(.002)
        rps=(count/float(w.get("pulses_per_rotation",3)))/float(w.get("sample_seconds",2))
        mps=round(rps*(2*math.pi*float(w.get("cup_radius_m",.04)))*float(w.get("calibration_factor",1)),1)
        return {"mps":mps,"message":f"GPIO{pin} {count}p"}
    except Exception: return {"mps":0,"message":"風速未読込"}
def read_rain():
    r=cfg().get("rain",{})
    if not r.get("enabled",False): return {"label":"未接続","message":"雨センサー未使用"}
    return {"label":"未接続","message":"GPIO未読込"}
@app.route("/")
def index():
    s=cfg(); return render_template("index.html",site_name=s["site_name"],version=s["version"])
@app.route("/api/status")
def status():
    s=cfg(); lp=latest_img(); mode=s["camera"].get("night_mode","auto"); active=night() if mode=="auto" else mode in ["low","medium","high","extreme","night"]; cp,cm=cloud(lp,active)
    ip=run("hostname -I | awk '{print $1}'",5).stdout.strip(); up=run("uptime -p",5).stdout.strip().replace("up ","")
    return jsonify(ok=True,version=s["version"],latest_image=lp.name if lp else None,recent_images=recent(),bme280=read_bme(),cloud=cp,cloud_message=cm,moon_age=round(moon_age()),sqm=20.6,wind=read_wind(),rain=read_rain(),system={"ip":ip,"uptime":up},night={"mode":mode,"active":active,"exposure_us":s["camera"].get("night_exposure_us",1800000),"gain":s["camera"].get("night_gain",20)})
@app.route("/api/night_mode",methods=["POST"])
def night_mode():
    mode=(request.get_json(force=True,silent=True) or {}).get("mode","auto")
    s=cfg(); s["camera"]["night_mode"]=mode; save_cfg(s); return jsonify(ok=True,message=f"星空モード: {mode}")
@app.route("/api/capture",methods=["POST"])
def capture():
    out=IMG/f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"; cmd=still_cmd(out)
    if not cmd: return jsonify(ok=False,message="カメラコマンドなし")
    r=run(cmd,120)
    return jsonify(ok=r.returncode==0 and out.exists(),filename=out.name,message="保存しました" if out.exists() else (r.stderr or "撮影失敗")[-800:])
@app.route("/api/video",methods=["POST"])
def video():
    return jsonify(ok=True,message="動画機能は次版で調整")
@app.route("/images/<path:n>")
def images(n): return send_from_directory(IMG,n)
@app.route("/videos/<path:n>")
def videos(n): return send_from_directory(VID,n)
if __name__=="__main__": app.run(host="0.0.0.0",port=5000)
