
from flask import Flask, jsonify, render_template, send_from_directory
from pathlib import Path
from datetime import datetime, timezone
import json, shutil, subprocess, platform, colorsys
BASE=Path(__file__).resolve().parents[1]; DATA=BASE/'data'; IMG=DATA/'images'; VID=DATA/'videos'; LOG=DATA/'logs'; CONFIG=BASE/'config/settings.json'
for p in (IMG,VID,LOG): p.mkdir(parents=True,exist_ok=True)
app=Flask(__name__,template_folder='templates',static_folder='static')
def cfg(): return json.loads(CONFIG.read_text(encoding='utf-8'))
def has_cmd(c): return shutil.which(c) is not None
def run(cmd,timeout=40): return subprocess.run(cmd,shell=True,text=True,capture_output=True,timeout=timeout)
def latest(folder,suffix):
    fs=sorted(folder.glob('*'+suffix),key=lambda p:p.stat().st_mtime,reverse=True); return fs[0].name if fs else None
def latest_path():
    n=latest(IMG,'.jpg'); return IMG/n if n else None
def recent_images(limit=5): return [p.name for p in sorted(IMG.glob('*.jpg'),key=lambda p:p.stat().st_mtime,reverse=True)[:limit]]
def moon_age():
    epoch=datetime(2000,1,6,18,14,tzinfo=timezone.utc); return round(((datetime.now(timezone.utc)-epoch).total_seconds()/86400)%29.53058867,1)
def camera_still_command(out):
    c=cfg().get('camera',{}); w=c.get('width',3072); h=c.get('height',3072); t=c.get('photo_timeout_ms',1000)
    if has_cmd('rpicam-still'): return f"rpicam-still -n --width {w} --height {h} --timeout {t} -o '{out}'"
    if has_cmd('libcamera-still'): return f"libcamera-still -n --width {w} --height {h} --timeout {t} -o '{out}'"
    return ''
def camera_video_command(out):
    t=cfg().get('camera',{}).get('video_time_ms',10000)
    if has_cmd('rpicam-vid'): return f"rpicam-vid -n -t {t} --width 1920 --height 1080 -o '{out}'"
    if has_cmd('libcamera-vid'): return f"libcamera-vid -n -t {t} --width 1920 --height 1080 -o '{out}'"
    return ''
def estimate_cloud_percent(path):
    try:
        from PIL import Image
        im=Image.open(path).convert('RGB'); im.thumbnail((720,720)); w,h=im.size; px=im.load(); cx=w/2; cy=h/2; r=min(w,h)*0.42
        sky=cloud=valid=unknown=0
        for y in range(h):
            for x in range(w):
                dx=x-cx; dy=y-cy
                if (dx*dx+dy*dy)**0.5>r: continue
                R,G,B=px[x,y]; mx=max(R,G,B); mn=min(R,G,B)
                if mx<35: continue
                if mx>245 and mx-mn<18: continue
                valid+=1; hh,ss,vv=colorsys.rgb_to_hsv(R/255,G/255,B/255); hue=hh*360; sat=ss*100; val=vv*100
                blue=(175<=hue<=245 and sat>=18 and val>=28 and B>=R+8 and B>=G-5)
                white=(sat<=34 and val>=45 and mx-mn<=70); gray=(sat<=28 and 28<=val<45); bright=(R>130 and G>130 and B>115 and sat<45)
                if blue: sky+=1
                elif white or gray or bright: cloud+=1
                else: unknown+=1
        if valid<500: return {'percent':33,'message':'雲量AI: 画像対象が少ないため仮値'}
        raw=(cloud+unknown*0.45)/valid*100; sr=sky/valid
        if sr<0.18 and raw<65: raw=70
        elif sr<0.30 and raw<50: raw=58
        return {'percent':int(max(0,min(100,round(raw)))),'message':f'雲量AI: sky={sky} cloud={cloud} unknown={unknown} valid={valid}'}
    except Exception as e: return {'percent':33,'message':'雲量AIエラー: '+str(e)}
def read_bme280():
    try:
        from smbus2 import SMBus
        from bme280 import BME280
        for bus_no in [1,10,13,14]:
            for addr in [0x76,0x77]:
                try:
                    dev=SMBus(bus_no)
                    try: s=BME280(i2c_dev=dev,i2c_addr=addr)
                    except TypeError: s=BME280(i2c_dev=dev)
                    temp=round(float(s.get_temperature()),1); hum=round(float(s.get_humidity()),1); press=round(float(s.get_pressure()),1)
                    try: dev.close()
                    except Exception: pass
                    return {'ok':True,'bus':bus_no,'address':hex(addr),'temperature':temp,'humidity':hum,'pressure':press,'message':f'BME280 正常 bus{bus_no} {hex(addr)}'}
                except Exception: pass
    except Exception as e: return {'ok':False,'message':'BME280ライブラリ読込失敗: '+str(e)}
    return {'ok':False,'message':'BME280を読めません'}
def system_info():
    ip=run("hostname -I | awk '{print $1}'",5).stdout.strip(); up=run('uptime -p',5).stdout.strip().replace('up ','')
    return {'ip':ip,'uptime':up,'camera':'正常' if has_cmd('rpicam-still') or has_cmd('libcamera-still') else '未確認'}
@app.route('/')
def index():
    s=cfg(); return render_template('index.html',site_name=s['site_name'],version=s['version'])
@app.route('/api/status')
def status():
    bme=read_bme280(); now=datetime.now(); lp=latest_path(); cloud=estimate_cloud_percent(lp) if lp and lp.exists() else {'percent':33,'message':'雲量AI:画像待機中'}
    return jsonify({'ok':True,'version':cfg()['version'],'time':now.strftime('%H:%M:%S'),'date':now.strftime('%Y/%m/%d'),'latest_image':lp.name if lp else None,'recent_images':recent_images(),'bme280':bme,'cloud':cloud['percent'],'cloud_message':cloud['message'],'moon_age':round(moon_age()),'sqm':20.6,'wind':{'mps':1.2,'direction':'西北西','degrees':292},'rain':{'label':'乾燥','message':'雨なし'},'system':system_info()})
@app.route('/api/capture',methods=['POST'])
def capture():
    name=f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"; out=IMG/name; cmd=camera_still_command(out)
    if not cmd: return jsonify({'ok':False,'message':'rpicam-still / libcamera-still が見つかりません'})
    r=run(cmd,60)
    if r.returncode!=0 or not out.exists(): return jsonify({'ok':False,'message':(r.stderr or r.stdout or '撮影失敗')[-1200:]})
    return jsonify({'ok':True,'filename':name,'message':f'保存しました: {name}'})
@app.route('/api/video',methods=['POST'])
def video(): return jsonify({'ok':True,'message':'動画機能は既存版を使用してください'})
@app.route('/images/<path:name>')
def images(name): return send_from_directory(IMG,name)
@app.route('/videos/<path:name>')
def videos(name): return send_from_directory(VID,name)
if __name__=='__main__': app.run(host='0.0.0.0',port=5000)
