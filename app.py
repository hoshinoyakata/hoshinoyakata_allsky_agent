from flask import Flask, render_template, jsonify, send_from_directory
from pathlib import Path
import subprocess, time, os

BASE = Path(__file__).resolve().parent
DATA = BASE / 'data'
CAPTURES = DATA / 'captures'
CAPTURES.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

CAMERA_CMD = os.environ.get('ALLSKY_CAMERA_CMD', 'rpicam-still')


def capture_image():
    filename = time.strftime('allsky_%Y%m%d_%H%M%S.jpg')
    out = CAPTURES / filename
    cmd = [CAMERA_CMD, '-n', '-t', '1000', '--width', '1600', '--height', '1200', '-o', str(out)]
    subprocess.run(cmd, check=True, timeout=15)
    return filename

@app.route('/')
def index():
    latest = get_latest()
    return render_template('index.html', latest=latest)

@app.route('/api/capture', methods=['POST'])
def api_capture():
    try:
        filename = capture_image()
        return jsonify({'ok': True, 'filename': filename, 'url': f'/captures/{filename}'})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/latest')
def api_latest():
    latest = get_latest()
    return jsonify({'ok': True, 'latest': latest, 'url': f'/captures/{latest}' if latest else None})

@app.route('/captures/<path:name>')
def captures(name):
    return send_from_directory(CAPTURES, name)


def get_latest():
    files = sorted(CAPTURES.glob('*.jpg'), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0].name if files else None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
