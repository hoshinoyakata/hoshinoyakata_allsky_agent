
from flask import Flask,jsonify,render_template,send_from_directory,request
from pathlib import Path
from datetime import datetime,timezone
import json,shutil,subprocess,time,math,colorsys,threading
BASE=Path(__file__).resolve().parents[1]
IMG=BASE/'data/images';VID=BASE/'data/videos';LOG=BASE/'data/logs';CONFIG=BASE/'config/settings.json';STATE=BASE/'data/state.json'
IMG.mkdir(parents=True,exist_ok=True);VID.mkdir(parents=True,exist_ok=True);LOG.mkdir(parents=True,exist_ok=True)
app=Flask(__name__,template_folder='templates',static_folder='static')
def cfg(): return json.loads(CONFIG.read_text(encoding='utf-8'))
def save_cfg(s): CONFIG.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
def state():
    if not STATE.exists(): STATE.write_text(json.dumps({'live':'on','recording':False,'camera_status':'live','ai':'on'},ensure_ascii=False,indent=2),encoding='utf-8')
    return json.loads(STATE.read_text(encoding='utf-8'))
def save_state(st): STATE.write_text(json.dumps(st,ensure_ascii=False,indent=2),encoding='utf-8')
def run(c,t=90): return subprocess.run(c,shell=True,text=True,capture_output=True,timeout=t)
def has(c): return shutil.which(c) is not None
def camtool(k): return 'rpicam-'+k if has('rpicam-'+k) else ('libcamera-'+k if has('libcamera-'+k) else '')
def night():
    h=datetime.now().hour; return h>=18 or h<=5
def latest_img():
    fs=sorted(IMG.glob('*.jpg'),key=lambda p:p.stat().st_mtime,reverse=True); return fs[0] if fs else None
def recent(n=5):
    return [p.name for p in sorted(IMG.glob('*.jpg'), key=lambda p: p.stat().st_mtime, reverse=True)[:n]]

def recent_detail(n=5):
    now = time.time()
    items = []
    for p in sorted(IMG.glob('*.jpg'), key=lambda p: p.stat().st_mtime, reverse=True)[:n]:
        mt = p.stat().st_mtime
        age = max(0, int(now - mt))
        if age < 60:
            age_label = f"{age}秒前"
        elif age < 3600:
            age_label = f"{age//60}分前"
        else:
            age_label = f"{age//3600}時間前"
        items.append({
            "name": p.name,
            "mtime": mt,
            "time": datetime.fromtimestamp(mt).strftime("%H:%M:%S"),
            "age": age,
            "age_label": age_label
        })
    return items
def moon_age():
    e=datetime(2000,1,6,18,14,tzinfo=timezone.utc); return round(((datetime.now(timezone.utc)-e).total_seconds()/86400)%29.53058867,1)
def still_cmd(out):
    s=cfg(); c=s['camera']; tool=camtool('still')
    if not tool: return ''
    mode=c.get('night_mode','auto'); active=night() if mode=='auto' else mode in ['low','medium','high','extreme','night']
    w,h=c.get('width',3072),c.get('height',3072)
    if mode=='day' or not active: return f"{tool} -n --width {w} --height {h} --timeout {c.get('photo_timeout_ms_day',1000)} -o '{out}'"
    presets={'low':(500000,8,1000),'medium':(1000000,14,1500),'high':(1800000,20,2500),'extreme':(3000000,26,3500),'auto':(c.get('night_exposure_us',1800000),c.get('night_gain',20),c.get('photo_timeout_ms_night',2500))}
    ex,g,t=presets.get(mode,presets['auto'])
    return f"{tool} -n --width {w} --height {h} --shutter {ex} --gain {g} --awbgains 1.35,1.55 --denoise cdn_hq --timeout {t} -o '{out}'"
def cloud(p,nightmode=False):
    if not p or not p.exists(): return 33,'画像待機中'
    try:
        from PIL import Image
        im=Image.open(p).convert('RGB'); im.thumbnail((640,640)); w,h=im.size; px=im.load(); cx,cy=w/2,h/2; r=min(w,h)*.42
        if nightmode:
            valid=stars=haze=0
            for y in range(1,h-1,2):
                for x in range(1,w-1,2):
                    if ((x-cx)**2+(y-cy)**2)**.5>r: continue
                    R,G,B=px[x,y]; mx=max(R,G,B); mn=min(R,G,B)
                    if mx<8: continue
                    valid+=1; ns=[max(px[xx,yy]) for yy in (y-1,y,y+1) for xx in (x-1,x,x+1)]
                    if mx>105 and mx>sum(ns)/len(ns)+24 and mx-mn<95: stars+=1
                    if 24<mx<175 and mx-mn<85: haze+=1
            if valid<300: return 50,'夜間雲量:画像不足'
            sr,hr=stars/valid,haze/valid
            return (85 if sr<.00008 and hr>.22 else 70 if sr<.00015 and hr>.12 else 55 if sr<.00035 else max(0,min(100,int(45-sr*80000+hr*45)))),f'夜間AI stars={stars}'
        valid=sky=cld=unk=0
        for y in range(h):
            for x in range(w):
                if ((x-cx)**2+(y-cy)**2)**.5>r: continue
                R,G,B=px[x,y]; mx=max(R,G,B); mn=min(R,G,B)
                if mx<35 or (mx>245 and mx-mn<18): continue
                valid+=1; hh,ss,vv=colorsys.rgb_to_hsv(R/255,G/255,B/255); hue=hh*360; sat=ss*100; val=vv*100
                blue=175<=hue<=245 and sat>=18 and val>=28 and B>=R+8
                white=sat<=34 and val>=45 and mx-mn<=70; gray=sat<=28 and 28<=val<45; bright=R>130 and G>130 and B>115 and sat<45
                if blue: sky+=1
                elif white or gray or bright: cld+=1
                else: unk+=1
        if valid<500: return 33,'雲量AI:対象不足'
        raw=(cld+unk*.45)/valid*100
        if sky/valid<.18 and raw<65: raw=70
        elif sky/valid<.30 and raw<50: raw=58
        return int(max(0,min(100,round(raw)))),'画像AI解析'
    except Exception: return 33,'雲量AIエラー'
def sea_level(station,alt): return station/((1-alt/44330.0)**5.255)
def pressure_fix(raw,alt=108,auto=True,offset=0.0):
    raw=float(raw); station=raw; unit='hPa'
    if auto and raw<850:
        station=raw*1.3332239; unit='mmHg→hPa'
    station+=float(offset); sea=sea_level(station,float(alt))
    return round(raw,2),unit,round(station,1),round(sea,1)
def read_bme():
    bs=cfg().get('bme280',{}); alt=float(bs.get('altitude_m',108)); auto=bool(bs.get('pressure_unit_auto_fix',True)); off=float(bs.get('pressure_offset_hpa',0))
    try:
        from smbus2 import SMBus
        from bme280 import BME280
        buses=[int(bs.get('bus',1))] if bs.get('bus','auto')!='auto' else [1,10,13,14]
        addrs=[0x76,0x77] if bs.get('address','auto')=='auto' else [int(str(bs.get('address')),0)]
        last=''
        for busno in buses:
            for addr in addrs:
                try:
                    bus=SMBus(busno)
                    try: sensor=BME280(i2c_dev=bus,i2c_addr=addr)
                    except TypeError: sensor=BME280(i2c_dev=bus)
                    temp=float(sensor.get_temperature()); hum=float(sensor.get_humidity()); raw=float(sensor.get_pressure())
                    rawv,unit,station,sea=pressure_fix(raw,alt,auto,off)
                    return {'ok':True,'temperature':round(temp,1),'humidity':round(hum,1),'pressure':sea,'station_pressure':station,'raw_pressure':rawv,'raw_unit':unit,'altitude_m':int(alt),'message':f'BME280 bus{busno} {hex(addr)}'}
                except Exception as e: last=str(e)
        return {'ok':False,'message':'BME280未読込: '+last}
    except Exception as e: return {'ok':False,'message':'BME280ライブラリ未読込: '+str(e)}
def read_wind():
    w=cfg().get('wind',{}); pin=int(w.get('gpio_pin',17))
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM); GPIO.setup(pin,GPIO.IN,pull_up_down=GPIO.PUD_UP)
        count=0; last=GPIO.input(pin); end=time.time()+float(w.get('sample_seconds',2)); deb=0
        while time.time()<end:
            now=GPIO.input(pin)
            if last==1 and now==0 and time.time()-deb>.02: count+=1; deb=time.time()
            last=now; time.sleep(.002)
        rps=(count/float(w.get('pulses_per_rotation',3)))/float(w.get('sample_seconds',2)); mps=round(rps*(2*math.pi*float(w.get('cup_radius_m',.04)))*float(w.get('calibration_factor',1)),1)
        return {'mps':mps,'deg':0,'gust':round(mps*1.8,1),'message':f'GPIO{pin} {count}p'}
    except Exception: return {'mps':0.0,'deg':0,'gust':0.0,'message':'風速未読込'}
def read_rain(): return {'label':'雨なし','message':'雨センサー未使用'}

def log(msg):
    return safe_log(msg)

def safe_log(msg):
    try:
        with (LOG / "system.log").open("a", encoding="utf-8") as f:
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "  " + str(msg) + "\n")
    except Exception:
        try:
            print(msg)
        except Exception:
            pass

CAPTURE_LOCK = threading.Lock()
AUTO_THREAD_STARTED = False

def cleanup_images():
    try:
        keep = int(cfg().get("camera", {}).get("keep_images", 1200))
        files = sorted(IMG.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in files[keep:]:
            try:
                p.unlink()
            except Exception:
                pass
    except Exception:
        pass

def do_capture(reason="auto"):
    """
    Ver.4.5:
    LIVE表示用にサーバー側で定期撮影する。
    ブラウザ側の2秒更新は「新しいjpgがあるか確認する」だけなので、
    ここで新しいjpgを作る。
    """
    with CAPTURE_LOCK:
        out = IMG / f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cmd = still_cmd(out)
        if not cmd:
            st = state()
            st["camera_status"] = "error"
            st["last_error"] = "カメラコマンドなし"
            save_state(st)
            safe_log(f"{reason}: カメラコマンドなし")
            return False, None, "カメラコマンドなし"

        r = run(cmd, 120)
        ok = (r.returncode == 0 and out.exists())
        st = state()
        if ok:
            st["camera_status"] = "live" if st.get("live") == "on" else "offline"
            st["last_error"] = ""
            save_state(st)
            cleanup_images()
            return True, out.name, "保存しました"
        else:
            st["camera_status"] = "error"
            st["last_error"] = (r.stderr or "撮影失敗")[-300:]
            save_state(st)
            safe_log(f"{reason}: 撮影失敗 {(r.stderr or '')[-300:]}")
            return False, None, (r.stderr or "撮影失敗")[-800:]

def auto_capture_loop():
    while True:
        try:
            s = cfg()
            c = s.get("camera", {})
            st = state()
            interval = max(2, int(c.get("live_capture_seconds", 5)))
            enabled = bool(c.get("auto_capture_enabled", True))
            live_on = st.get("live", "on") == "on"
            recording = bool(st.get("recording", False))

            if enabled and live_on and not recording:
                do_capture("auto-live")
                time.sleep(interval)
            else:
                time.sleep(2)
        except Exception as e:
            safe_log("auto_capture_loop error: " + str(e))
            time.sleep(5)

def start_auto_capture_once():
    global AUTO_THREAD_STARTED
    if AUTO_THREAD_STARTED:
        return
    AUTO_THREAD_STARTED = True
    th = threading.Thread(target=auto_capture_loop, daemon=True)
    th.start()
    safe_safe_log("Ver.4.6 auto live capture thread started")

start_auto_capture_once()


@app.route('/')
def index():
    s=cfg(); return render_template('index.html',site_name=s['site_name'],version=s['version'])
@app.route('/api/status')
def status():
    s=cfg(); st=state(); lp=latest_img(); mode=s['camera'].get('night_mode','auto'); active=night() if mode=='auto' else mode in ['low','medium','high','extreme','night']; cp,cm=cloud(lp,active)
    ip=run("hostname -I | awk '{print $1}'",5).stdout.strip(); up=run('uptime -p',5).stdout.strip().replace('up ','')
    return jsonify(ok=True,version=s['version'],latest_image=lp.name if lp else None,latest_mtime=lp.stat().st_mtime if lp else None,recent_images=recent_detail(),live_capture_seconds=s.get("camera",{}).get("live_capture_seconds",5),auto_capture_enabled=s.get("camera",{}).get("auto_capture_enabled",True),bme280=read_bme(),cloud=cp,cloud_message=cm,moon_age=round(moon_age()),sqm=20.6,wind=read_wind(),rain=read_rain(),system={'ip':ip,'uptime':up},live=st.get('live','on'),recording=st.get('recording',False),camera_status=st.get('camera_status','live'),night={'mode':mode,'active':active,'exposure_us':s['camera'].get('night_exposure_us',1800000),'gain':s['camera'].get('night_gain',20)})
@app.route('/api/control',methods=['POST'])
def control():
    action=(request.get_json(force=True,silent=True) or {}).get('action',''); st=state(); msg='操作しました'
    if action=='live_on': st['live']='on'; st['camera_status']='live'; msg='ライブ開始'
    elif action=='live_off': st['live']='off'; st['camera_status']='offline'; msg='ライブ停止'
    elif action=='record_start': st['recording']=True; st['camera_status']='recording'; msg='録画中'
    elif action=='record_stop': st['recording']=False; st['camera_status']='live' if st.get('live')=='on' else 'offline'; msg='録画停止'
    elif action=='ai_on': st['ai']='on'; msg='AI解析ON'
    elif action=='ai_off': st['ai']='off'; msg='AI解析OFF'
    save_state(st); return jsonify(ok=True,message=msg,state=st)
@app.route('/api/night_mode',methods=['POST'])
def night_mode():
    mode=(request.get_json(force=True,silent=True) or {}).get('mode','auto'); s=cfg(); s['camera']['night_mode']=mode; save_cfg(s); return jsonify(ok=True,message=f'星空感度: {mode}')
@app.route("/api/capture", methods=["POST"])
def capture():
    st = state()
    st["camera_status"] = "capture"
    save_state(st)
    ok, filename, msg = do_capture("manual")
    return jsonify(ok=ok, filename=filename, message=msg)

@app.route('/api/video',methods=['POST'])
def video():
    st=state(); st['recording']=True; st['camera_status']='recording'; save_state(st); return jsonify(ok=True,message='録画開始状態にしました')
@app.route('/images/<path:n>')
def images(n): return send_from_directory(IMG,n)
@app.route('/videos/<path:n>')
def videos(n): return send_from_directory(VID,n)
if __name__=='__main__': app.run(host='0.0.0.0',port=5000)
