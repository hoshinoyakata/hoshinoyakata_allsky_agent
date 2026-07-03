
let latestImage=null;
let timer=null;

function $(id){return document.getElementById(id)}
function text(id,v){const e=$(id); if(e) e.textContent=v}

function tick(){
  const d=new Date();
  text("clock", d.toLocaleTimeString("ja-JP",{hour12:false}));
  text("date", d.toLocaleDateString("ja-JP",{year:"numeric",month:"2-digit",day:"2-digit",weekday:"short"}));
}
setInterval(tick,1000); tick();

async function loadStatus(force=false){
  try{
    const r=await fetch("/api/status?ts="+Date.now());
    const s=await r.json();

    if(s.latest_image && (force || s.latest_image!==latestImage)){
      latestImage=s.latest_image;
      refreshImage();
      renderThumbs(s.latest_image);
    }

    const b=s.bme280||{};
    if(b.ok){
      text("temp", `${b.temperature}℃`);
      text("hum", `${b.humidity}%`);
      text("press", `${b.pressure} hPa`);
      text("metaTemp", `${b.temperature}℃`);
      text("sensorMsg", b.message || "BME280正常");
    }else{
      text("temp", "未読込");
      text("hum", "未読込");
      text("press", "未読込");
      text("sensorMsg", b.message || "BME280未読込");
    }

    text("cloud", `${s.cloud}%`);
    text("moon", Math.round(Number(s.moon_age)||0));
    text("moon2", Math.round(Number(s.moon_age)||0));
    text("sqm", s.sqm);
    text("wind", `${(s.wind||{}).mps ?? 0} m/s`);
    renderSystem(s.system||{});
  }catch(e){
    text("message", "状態取得エラー: "+e);
  }
}

function refreshImage(){
  if(!latestImage) return;
  const img=$("sky"), viewer=$("viewer");
  img.onload=()=>{viewer.classList.add("has-image");}
  img.onerror=()=>{viewer.classList.remove("has-image"); text("empty","画像読込失敗");}
  img.src=`/images/${latestImage}?ts=${Date.now()}`;
}

async function capture(){
  text("message","撮影中...");
  const r=await fetch("/api/capture",{method:"POST"});
  const j=await r.json();
  if(j.ok){latestImage=j.filename; text("message",j.message); refreshImage(); renderThumbs(j.filename);}
  else text("message","撮影失敗: "+j.message);
}

async function recordVideo(){
  text("message","動画撮影中...");
  const r=await fetch("/api/video",{method:"POST"});
  const j=await r.json();
  text("message",j.message || "動画処理完了");
}

function toggleFullscreen(){
  const el=$("viewer");
  if(!document.fullscreenElement) el.requestFullscreen?.();
  else document.exitFullscreen?.();
}

function renderSystem(s){
  const el=$("systemInfo"); if(!el)return;
  el.innerHTML = `
    <div><span>CPU温度</span><span>--</span></div>
    <div><span>稼働時間</span><span>${esc(s.uptime||"--")}</span></div>
    <div><span>IPアドレス</span><span>${esc(s.ip||"--")}</span></div>
    <div><span>ストレージ</span><span>${esc(s.storage||"--")}</span></div>
    <div><span>カメラ</span><span>正常</span></div>
    <div><span>センサー</span><span>正常</span></div>
  `;
}

function renderThumbs(filename){
  const el=$("thumbs"); if(!el || !filename)return;
  const now=new Date();
  let html="";
  for(let i=0;i<4;i++){
    const t=new Date(now.getTime()-i*10*60000);
    html += `<div class="thumb"><img src="/images/${filename}?thumb=${i}&ts=${Date.now()}"><small>${t.toLocaleTimeString("ja-JP",{hour:"2-digit",minute:"2-digit"})}</small></div>`;
  }
  el.innerHTML=html;
}

function esc(s){return String(s).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[m]))}

loadStatus(true);
timer=setInterval(loadStatus,2000);
