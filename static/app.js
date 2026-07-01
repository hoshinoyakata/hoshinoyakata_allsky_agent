const msg = document.getElementById('message');
const img = document.getElementById('sky');

document.getElementById('captureBtn').addEventListener('click', async () => {
  msg.textContent = '撮影中です...';
  try {
    const res = await fetch('/api/capture', {method:'POST'});
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || '撮影に失敗しました');
    img.src = data.url + '?t=' + Date.now();
    msg.textContent = '保存しました: ' + data.filename;
  } catch(e) {
    msg.textContent = 'エラー: ' + e.message;
  }
});

document.getElementById('refreshBtn').addEventListener('click', async () => {
  const res = await fetch('/api/latest');
  const data = await res.json();
  if(data.url){ img.src = data.url + '?t=' + Date.now(); msg.textContent='最新画像に更新しました'; }
  else msg.textContent='まだ画像がありません。写真を撮影してください。';
});

document.getElementById('fullBtn').addEventListener('click', () => {
  document.querySelector('.sky-circle').requestFullscreen?.();
});
