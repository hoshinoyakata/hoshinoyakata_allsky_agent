function reloadImage(){document.getElementById('sky').src='/image/latest?t='+Date.now();}
async function captureImage(){
  const m=document.getElementById('message'); m.textContent='撮影中...';
  const r=await fetch('/capture',{method:'POST'}); const j=await r.json();
  m.textContent=j.ok ? '保存しました: '+j.file : '失敗しました';
  reloadImage(); loadStatus(); loadList();
}
function fullscreenSky(){const el=document.querySelector('.skywrap'); if(el.requestFullscreen) el.requestFullscreen();}
async function updateSystem(){
  const m=document.getElementById('message'); m.textContent='GitHubから更新中...';
  const r=await fetch('/api/update',{method:'POST'}); const j=await r.json();
  m.textContent=j.ok ? '更新しました。必要なら再起動してください。' : '更新失敗: '+j.message;
}
async function loadStatus(){
  const r=await fetch('/api/status?t='+Date.now()); const s=await r.json();
  document.getElementById('clock').textContent=s.time;
  document.getElementById('ver').textContent=s.version;
  document.getElementById('git').textContent=(s.git.commit||'--')+' '+(s.git.branch||'');
  document.getElementById('moonAge').textContent=s.moon_age;
  document.getElementById('moonLabel').textContent=s.moon_label;
  document.getElementById('cloud').textContent=s.cloud.cloud===null?'--%':s.cloud.cloud+'%';
  document.getElementById('cloudMsg').textContent=s.cloud.message;
  document.getElementById('temp').textContent=s.bme280.temperature===null?'準備中':s.bme280.temperature+'℃';
  document.getElementById('hum').textContent=s.bme280.humidity===null?'準備中':s.bme280.humidity+'%';
  document.getElementById('press').textContent=s.bme280.pressure===null?'準備中':s.bme280.pressure+'hPa';
}
async function loadList(){
  const r=await fetch('/api/list?t='+Date.now()); const arr=await r.json();
  const box=document.getElementById('thumbs'); box.innerHTML='';
  arr.forEach(x=>{const d=document.createElement('div'); d.innerHTML=`<img src="${x.url}"><span>${x.mtime}</span>`; box.appendChild(d);});
}
setInterval(()=>{loadStatus();},3000); loadStatus(); loadList();
