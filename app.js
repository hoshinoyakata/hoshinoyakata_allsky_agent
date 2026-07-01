function reloadImage(){document.getElementById('sky').src='/image?t='+Date.now();}
setInterval(reloadImage, 2500);
async function captureStill(){const r=await fetch('/capture',{method:'POST'}); const j=await r.json(); alert(j.ok?'保存しました: '+j.file:'失敗: '+j.message); location.reload();}
async function record10(){const r=await fetch('/record10',{method:'POST'}); const j=await r.json(); alert(j.ok?'録画しました: '+j.file:'失敗: '+j.message);}
function fullscreenSky(){const el=document.getElementById('skybox'); if(el.requestFullscreen) el.requestFullscreen();}
async function updateStatus(){try{const r=await fetch('/status'); const j=await r.json(); document.getElementById('status').textContent=JSON.stringify(j,null,2);}catch(e){}}
setInterval(updateStatus,3000); updateStatus();
