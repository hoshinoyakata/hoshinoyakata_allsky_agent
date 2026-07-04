
let latestImage=null;
let latestMtime=null;

function $(id){return document.getElementById(id)}
function setText(id,v){const e=$(id);if(e)e.textContent=v}

function updateClock(){
  const d=new Date();
  setText("timeText",d.toLocaleTimeString("ja-JP",{hour12:false}));
  setText("dateText",d.toLocaleDateString("ja-JP",{year:"numeric",month:"2-digit",day:"2-digit",weekday:"short"}));
}
setInterval(updateClock,1000);
updateClock();

function setLiveBadge(status,recording,live){
  const b=$("liveBadge"); if(!b)return;
  b.className="liveBadge";
  if(recording||status==="recording"){b.classList.add("live-rec");b.textContent="● REC";setText("cameraState","REC");return;}
  if(status==="capture"){b.classList.add("live-capture");b.textContent="● CAPTURE";setText("cameraState","CAPTURE");return;}
  if(status==="error"){b.classList.add("live-error");b.textContent="● ERROR";setText("cameraState","ERROR");return;}
  if(live==="off"||status==="offline"){b.classList.add("live-off");b.textContent="○ OFFLINE";setText("cameraState","OFFLINE");return;}
  b.classList.add("live-on");b.textContent="● LIVE";setText("cameraState","LIVE");
}

function sameMtime(a,b){
  if(a==null || b==null) return false;
  return Math.abs(Number(a)-Number(b)) < 0.001;
}

async function loadStatus(force=false){
  try{
    const s=await (await fetch("/api/status?ts="+Date.now(), {cache:"no-store"})).json();

    const imageChanged = s.latest_image && (
      force ||
      s.latest_image !== latestImage ||
      !sameMtime(s.latest_mtime, latestMtime)
    );

    if(imageChanged){
      latestImage=s.latest_image;
      latestMtime=s.latest_mtime;
      refreshImage();
    }

    renderThumbs(s.recent_images||[]);

    if(s.latest_mtime){
      const d=new Date(Number(s.latest_mtime)*1000);
      setText("lastImageTime", d.toLocaleTimeString("ja-JP",{hour12:false}));
    }

    const b=s.bme280||{};
    if(b.ok){
      setText("temp",`${b.temperature}℃`);
      setText("hum",`${b.humidity}%`);
      setText("press",`${b.pressure} hPa`);
      setText("pressDetail",`現地 ${b.station_pressure} / raw ${b.raw_pressure} ${b.raw_unit} / 標高${b.altitude_m}m`);
    }else{
      setText("temp","--");
      setText("hum","--");
      setText("press","--");
      setText("pressDetail",b.message||"BME280未読込");
    }

    setText("cloud",`${s.cloud}%`);
    setText("cloudMsg",s.cloud_message||"解析中");
    setText("moon",s.moon_age);
    setText("moon2",s.moon_age);
    setText("sqm",s.sqm);

    const w=s.wind||{};
    setText("wind",`${w.mps??0} m/s`);
    setText("windMsg",w.message||"--");
    setText("windDeg",`${w.deg??0}°`);
    setText("gust",`${w.gust??0} m/s`);

    const r=s.rain||{};
    setText("rain",r.label||"--");

    const sys=s.system||{};
    setText("uptime",sys.uptime||"--");
    setText("ip",sys.ip||"--");

    const n=s.night||{};
    setText("exposureLabel",n.exposure_us?`${Math.round(n.exposure_us/100000)/10} sec`:"AUTO");
    setText("gainLabel",n.gain?`${n.gain}.0 dB`:"AUTO");

    setLiveBadge(s.camera_status,s.recording,s.live);
  }catch(e){
    setText("message","状態取得エラー: "+e);
  }
}

function refreshImage(){
  if(!latestImage)return;
  const img=$("sky"), viewer=$("viewer");
  img.onload=()=>viewer.classList.add("hasImage");
  img.onerror=()=>viewer.classList.remove("hasImage");
  img.src=`/images/${latestImage}?mtime=${encodeURIComponent(latestMtime||"")}&ts=${Date.now()}`;
}

async function capture(){
  setText("message","撮影中...");
  const j=await (await fetch("/api/capture",{method:"POST",cache:"no-store"})).json();
  if(j.ok){
    latestImage=null;
    latestMtime=null;
    setText("message",j.message);
    loadStatus(true);
  }else{
    setText("message","撮影失敗: "+j.message);
  }
}

async function recordStart(){
  await control("record_start");
  await fetch("/api/video",{method:"POST",cache:"no-store"});
  loadStatus(true);
}
async function recordStop(){await control("record_stop");}

async function control(action){
  const j=await (await fetch("/api/control",{
    method:"POST",
    cache:"no-store",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({action})
  })).json();
  setText("message",j.message||"操作しました");
  loadStatus(true);
}

async function setNightMode(mode){
  const j=await (await fetch("/api/night_mode",{
    method:"POST",
    cache:"no-store",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({mode})
  })).json();
  setText("message",j.message||"変更しました");
  loadStatus(true);
}


function toggleFullscreen(){
  const el=$("viewer");
  if(!document.fullscreenElement){
    el.classList.add("fullscreen-active");
    const req=el.requestFullscreen||el.webkitRequestFullscreen||el.msRequestFullscreen;
    if(req) req.call(el);
  }else{
    const exit=document.exitFullscreen||document.webkitExitFullscreen||document.msExitFullscreen;
    if(exit) exit.call(document);
  }
}

document.addEventListener("fullscreenchange",()=>{
  const el=$("viewer");
  if(!document.fullscreenElement && el) el.classList.remove("fullscreen-active");
});
document.addEventListener("webkitfullscreenchange",()=>{
  const el=$("viewer");
  if(!document.webkitFullscreenElement && el) el.classList.remove("fullscreen-active");
});


function renderThumbs(items){
  const el=$("thumbs"); if(!el)return;
  if(!items.length){
    el.innerHTML="<small>まだ保存画像がありません</small>";
    return;
  }
  el.innerHTML=items.slice(0,5).map((it,i)=>{
    const name = typeof it === "string" ? it : it.name;
    const label = typeof it === "string" ? (i===0 ? "最新" : "") : `${it.time}`;
    const age = typeof it === "string" ? "" : `<em>${it.age_label}</em>`;
    return `<div class="thumb"><img src="/images/${name}?mtime=${encodeURIComponent(it.mtime||"")}&ts=${Date.now()}"><small>${i===0?"最新 ":""}${label}</small>${age}</div>`;
  }).join("");
}

loadStatus(true);
setInterval(()=>loadStatus(false),2000);
