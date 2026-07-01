async function refresh(){
  const r = await fetch('/api/status');
  const s = await r.json();
  document.getElementById('time').textContent = s.time;
  document.getElementById('condition').textContent = s.condition;
  document.getElementById('temp').textContent = s.sensor.temperature + '℃';
  document.getElementById('hum').textContent = s.sensor.humidity + '%';
  document.getElementById('press').textContent = s.sensor.pressure + 'hPa';
  document.getElementById('cloud').textContent = (s.cloud_percent ?? '--') + '%';
  document.getElementById('moon').textContent = s.moon.age + ' / ' + s.moon.phase;
  document.getElementById('sqm').textContent = s.sqm;
  document.getElementById('sky').src = s.latest_url + '?t=' + Date.now();
  loadGallery();
}
async function capture(){
  await fetch('/api/capture', {method:'POST'});
  refresh();
}
async function record(){
  const r = await fetch('/api/record', {method:'POST'});
  const s = await r.json();
  alert(s.message);
}
async function loadGallery(){
  const r = await fetch('/api/recent');
  const imgs = await r.json();
  const g = document.getElementById('gallery');
  g.innerHTML = imgs.map(i => `<img src="${i.url}?t=${Date.now()}" title="${i.name}">`).join('');
}
function toggleFullscreen(){
  const el = document.querySelector('.sky-card');
  if(!document.fullscreenElement){ el.requestFullscreen(); } else { document.exitFullscreen(); }
}
refresh();
setInterval(refresh, 15000);
