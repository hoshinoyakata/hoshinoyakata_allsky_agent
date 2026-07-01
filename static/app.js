async function jsonFetch(url, options={}){
  const r = await fetch(url, options);
  return await r.json();
}
function setText(id, text){ const e=document.getElementById(id); if(e) e.textContent=text; }
function msg(t){ setText('message', t); }
async function updateStatus(){
  try{
    const s = await jsonFetch('/status');
    setText('version', s.version || '-');
    setText('now', s.time || '-');
    if(s.latest_url){ document.getElementById('sky').src = s.latest_url + '?t=' + Date.now(); }
    setText('cloud', (s.cloud ?? '--') + '%');
    setText('moon', s.moon_age ?? '--');
    setText('moonLabel', s.moon_label || '');
    setText('sqm', s.sqm ?? '--');
    setText('score', s.observation?.score ?? '--');
    setText('scoreLabel', s.observation?.label || '監視中');
    if(s.bme280?.ok){
      setText('temp', s.bme280.temperature + '℃');
      setText('hum', s.bme280.humidity + '%');
      setText('press', s.bme280.pressure + 'hPa');
    } else {
      setText('temp', '準備中'); setText('hum', '準備中'); setText('press', '準備中');
    }
    setText('rain', s.rain?.label || s.rain?.message || '未設定');
    const cap = document.getElementById('captures');
    cap.innerHTML = (s.captures||[]).map(x=>`<a href="/images/${x}" target="_blank">${x}</a>`).join('') || 'まだありません';
    const vid = document.getElementById('videos');
    vid.innerHTML = (s.videos||[]).map(x=>`<a href="/videos/${x}" target="_blank">${x}</a>`).join('') || 'まだありません';
  }catch(e){ msg('状態取得エラー: '+e); }
}
async function captureNow(){
  msg('撮影中...');
  const r = await jsonFetch('/capture', {method:'POST'});
  msg(r.ok ? '保存しました: '+r.file : '失敗: '+r.message);
  await updateStatus();
}
async function makeVideo(){
  msg('MP4作成中...');
  const r = await jsonFetch('/video', {method:'POST'});
  msg(r.ok ? '動画を作成しました: '+r.file : '失敗: '+r.message);
  await updateStatus();
}
async function runUpdate(){
  if(!confirm('GitHubから最新版に更新しますか？')) return;
  const r = await jsonFetch('/update', {method:'POST'});
  msg(r.message || '更新を開始しました');
}
function reloadImage(){ updateStatus(); }
function fullscreenSky(){
  const el = document.getElementById('skybox');
  if(el.requestFullscreen) el.requestFullscreen();
}
updateStatus();
setInterval(updateStatus, 3000);
