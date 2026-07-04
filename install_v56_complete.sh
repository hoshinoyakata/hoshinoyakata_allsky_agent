#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "=== Hoshinoyakata Allsky Ver5.6 NAS MP4 Web Complete installer ==="
mkdir -p scripts data web
cp -f scripts/mp4_record_nas.py ./scripts/mp4_record_nas.py
chmod +x ./scripts/mp4_record_nas.py

# NAS folders / symlinks
NAS_BASE="/mnt/hoshinoyakata_nas/全天カメラ"
mkdir -p "$NAS_BASE/MP4動画" "$NAS_BASE/システムログ" || true
if [ -d data/videos ] && [ ! -L data/videos ]; then mv data/videos "data/videos_local_backup_$(date +%Y%m%d_%H%M%S)"; fi
if [ ! -L data/videos ]; then ln -s "$NAS_BASE/MP4動画" data/videos; fi
if [ -d data/logs ] && [ ! -L data/logs ]; then mv data/logs "data/logs_local_backup_$(date +%Y%m%d_%H%M%S)"; fi
if [ ! -L data/logs ]; then ln -s "$NAS_BASE/システムログ" data/logs; fi

# patch web/app.py to add MP4 API + light UI injection
APP="web/app.py"
if [ -f "$APP" ]; then
  cp "$APP" "$APP.bak_v56_$(date +%Y%m%d_%H%M%S)"
  if ! grep -q "HOSHI_V56_MP4_WEB_PATCH" "$APP"; then
cat >> "$APP" <<'PYAPP'

# ===== HOSHI_V56_MP4_WEB_PATCH START =====
# Adds MP4 recording API and injects a working button into existing Ver5.4 UI.
from pathlib import Path as _HoshiPath
import subprocess as _hoshi_subprocess, json as _hoshi_json, time as _hoshi_time, os as _hoshi_os
try:
    from flask import jsonify as _hoshi_jsonify, send_from_directory as _hoshi_send_from_directory, request as _hoshi_request
except Exception:
    _hoshi_jsonify = None

_HOSHI_BASE = _HoshiPath(__file__).resolve().parents[1]
_HOSHI_NAS_BASE = _HoshiPath(_hoshi_os.environ.get("HOSHI_NAS_BASE", "/mnt/hoshinoyakata_nas/全天カメラ"))
_HOSHI_VIDEO_DIR = _HoshiPath(_hoshi_os.environ.get("HOSHI_VIDEO_DIR", str(_HOSHI_NAS_BASE / "MP4動画")))
_HOSHI_STATUS = _HOSHI_BASE / "data" / "mp4_record_status.json"
_HOSHI_PROC = {"p": None, "started": 0}

def _hoshi_status_dict():
    if _HOSHI_STATUS.exists():
        try:
            return _hoshi_json.loads(_HOSHI_STATUS.read_text(encoding="utf-8"))
        except Exception:
            pass
    p = _HOSHI_PROC.get("p")
    return {"ok": True, "recording": bool(p and p.poll() is None), "message": "idle"}

@app.route('/api/mp4/start', methods=['POST','GET'])
def hoshi_v56_mp4_start():
    p = _HOSHI_PROC.get("p")
    if p and p.poll() is None:
        return _hoshi_jsonify({"ok": False, "recording": True, "message": "すでに録画中です"})
    try:
        seconds = int((_hoshi_request.values.get('seconds') if _hoshi_request else None) or 30)
    except Exception:
        seconds = 30
    seconds = max(5, min(seconds, 1800))
    cmd = [str(_HOSHI_BASE / 'venv' / 'bin' / 'python') if (_HOSHI_BASE/'venv/bin/python').exists() else 'python3',
           str(_HOSHI_BASE / 'scripts' / 'mp4_record_nas.py'), '--seconds', str(seconds)]
    _HOSHI_PROC['p'] = _hoshi_subprocess.Popen(cmd, cwd=str(_HOSHI_BASE), stdout=_hoshi_subprocess.DEVNULL, stderr=_hoshi_subprocess.DEVNULL)
    _HOSHI_PROC['started'] = _hoshi_time.time()
    return _hoshi_jsonify({"ok": True, "recording": True, "seconds": seconds, "message": "録画開始"})

@app.route('/api/mp4/status')
def hoshi_v56_mp4_status():
    st = _hoshi_status_dict()
    p = _HOSHI_PROC.get("p")
    if p and p.poll() is None:
        st["recording"] = True
    return _hoshi_jsonify(st)

@app.route('/api/mp4/list')
def hoshi_v56_mp4_list():
    _HOSHI_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(_HOSHI_VIDEO_DIR.glob('*.mp4'), key=lambda x: x.stat().st_mtime, reverse=True)[:30]
    return _hoshi_jsonify({"ok": True, "files": [{"name": f.name, "size": f.stat().st_size, "mtime": f.stat().st_mtime, "url": "/mp4/"+f.name} for f in files]})

@app.route('/mp4/<path:name>')
def hoshi_v56_mp4_file(name):
    return _hoshi_send_from_directory(str(_HOSHI_VIDEO_DIR), name)

try:
    @app.after_request
    def hoshi_v56_inject_mp4_ui(resp):
        try:
            ct = resp.headers.get('content-type','')
            if 'text/html' not in ct.lower():
                return resp
            html = resp.get_data(as_text=True)
            if 'HOSHI_V56_MP4_UI' in html:
                return resp
            html = html.replace('動画録画（準備中）', '🎥 MP4録画 30秒')
            html = html.replace('動画録画は準備中です。今は静止画ライブを優先しています。', 'MP4録画できます。NASのMP4動画フォルダへ保存します。')
            js = r'''
<script id="HOSHI_V56_MP4_UI">
(function(){
  function findBtn(){
    const nodes=[...document.querySelectorAll('button,a,div')];
    return nodes.find(x => (x.innerText||'').includes('MP4録画') || (x.innerText||'').includes('動画録画'));
  }
  async function refreshList(){
    try{
      const r=await fetch('/api/mp4/list'); const j=await r.json();
      let box=document.getElementById('hoshi-mp4-list');
      if(!box){ box=document.createElement('div'); box.id='hoshi-mp4-list'; box.style.cssText='margin-top:8px;font-size:12px;line-height:1.4;color:#dbeafe;'; const b=findBtn(); if(b&&b.parentNode)b.parentNode.appendChild(box); }
      box.innerHTML='<b>最新MP4</b><br>'+(j.files||[]).slice(0,5).map(f=>'<a style="color:#93c5fd" target="_blank" href="'+f.url+'">▶ '+f.name+'</a>').join('<br>');
    }catch(e){}
  }
  function setup(){
    const b=findBtn(); if(!b || b.dataset.hoshiMp4) return;
    b.dataset.hoshiMp4='1'; b.innerText='🎥 MP4録画 30秒'; b.style.cursor='pointer'; b.style.opacity='1'; b.disabled=false;
    b.onclick=async function(ev){ ev.preventDefault(); b.innerText='⏺ 録画開始中...';
      try{ const r=await fetch('/api/mp4/start?seconds=30',{method:'POST'}); const j=await r.json(); b.innerText=j.ok?'⏺ 録画中 30秒':'⚠ '+(j.message||'録画不可'); setTimeout(()=>{ b.innerText='🎥 MP4録画 30秒'; refreshList(); }, 36000); }
      catch(e){ b.innerText='⚠ 録画エラー'; }
    };
    refreshList(); setInterval(refreshList, 30000);
  }
  setInterval(setup,1000); document.addEventListener('DOMContentLoaded',setup);
})();
</script>
'''
            html = html.replace('</body>', js+'</body>') if '</body>' in html else html+js
            resp.set_data(html)
            resp.headers['content-length'] = str(len(resp.get_data()))
        except Exception:
            pass
        return resp
except Exception:
    pass
# ===== HOSHI_V56_MP4_WEB_PATCH END =====
PYAPP
  fi
else
  echo "WARNING: web/app.py が見つかりません。APIボタンパッチは未適用です。"
fi

# ensure scripts are executable
chmod +x scripts/mp4_record_nas.py

echo "=== Ver5.6 install complete ==="
echo "次に実行: sudo systemctl restart hoshinoyakata-allsky.service && sudo systemctl restart hoshinoyakata-capture.service"
