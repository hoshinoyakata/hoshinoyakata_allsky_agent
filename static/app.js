async function api(url, opt={}){ const r=await fetch(url,opt); return await r.json(); }
function $(id){return document.getElementById(id)}
async function refreshStatus(){
 const s=await api('/status'); $('clock').textContent=s.time; $('time').textContent=s.time;
 if(s.latest_url){ $('sky').src=s.latest_url+'?t='+Date.now(); }
 $('cloud').textContent=s.cloud ?? '--'; $('moon').textContent=s.moon_age; $('moonLabel').textContent=s.moon_label;
 $('sqm').textContent=s.sqm ?? '--';
 const b=s.bme280||{}; $('temp').textContent=b.temperature==null?'準備中':b.temperature+'℃'; $('hum').textContent=b.humidity==null?'準備中':b.humidity+'%'; $('press').textContent=b.pressure==null?'準備中':b.pressure+'hPa';
 $('thumbs').innerHTML=(s.captures||[]).map(f=>`<img src="/images/${f}?t=${Date.now()}" title="${f}">`).join('');
 $('videos').innerHTML=(s.videos||[]).map(f=>`<a href="/videos/${f}" target="_blank">${f}</a>`).join('<br>')||'まだありません';
}
async function capture(){ $('message').textContent='撮影中...'; const j=await api('/capture',{method:'POST'}); $('message').textContent=j.ok?'保存しました: '+j.file:'失敗: '+j.message; await refreshStatus(); }
async function video(){ $('message').textContent='MP4作成中...'; const j=await api('/video',{method:'POST'}); $('message').innerHTML=j.ok?`MP4作成: <a href="${j.url}" target="_blank">${j.file}</a>`:'失敗: '+j.message; await refreshStatus(); }
async function updateNow(){ if(!confirm('GitHubから更新しますか？')) return; const j=await api('/update',{method:'POST'}); alert(j.message||JSON.stringify(j)); }
function full(){ const el=document.querySelector('.skywrap'); if(el.requestFullscreen) el.requestFullscreen(); }
setInterval(refreshStatus,3000); refreshStatus();
