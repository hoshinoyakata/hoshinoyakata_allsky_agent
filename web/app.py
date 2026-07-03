from __future__ import annotations
from flask import Flask, jsonify, render_template, send_from_directory
from pathlib import Path
from datetime import datetime, timezone
import json, subprocess

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / 'data'
IMG = DATA / 'images'
CONFIG = BASE / 'config' / 'settings.json'
IMG.mkdir(parents=True, exist_ok=True)
app = Flask(__name__, template_folder='templates', static_folder='static')

def settings():
    return json.loads(CONFIG.read_text(encoding='utf-8'))

def latest_image():
    files = sorted(IMG.glob('*.jpg'), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0].name if files else None

def moon_age():
    epoch = datetime(2000,1,6,18,14,tzinfo=timezone.utc)
    days = (datetime.now(timezone.utc)-epoch).total_seconds()/86400
    return round(days % 29.53058867, 1)

def read_bme280():
    cfg = settings().get('bme280', {})
    try:
        from smbus2 import SMBus
        from bme280 import BME280
        address = int(cfg.get('address','0x76'), 16)
        sensor = BME280(i2c_dev=SMBus(int(cfg.get('bus',1))), address=address)
        return {'ok': True, 'temperature': round(sensor.get_temperature(),1), 'humidity': round(sensor.get_humidity(),1), 'pressure': round(sensor.get_pressure(),1), 'address': hex(address)}
    except Exception as e:
        return {'ok': False, 'message': str(e)}

@app.route('/')
def index():
    return render_template('index.html', version=settings().get('version','1.3-dev'))

@app.route('/api/status')
def api_status():
    return jsonify({'time': datetime.now().strftime('%Y/%m/%d %H:%M:%S'), 'latest_image': latest_image(), 'bme280': read_bme280(), 'moon_age': moon_age(), 'sqm': 20.8, 'cloud': 33, 'wind_mps': 0.0})

@app.route('/api/capture', methods=['POST'])
def api_capture():
    name = f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    out = IMG / name
    cmd = settings()['camera']['capture_command'].format(output=str(out))
    try:
        r = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=25)
        if r.returncode != 0:
            return jsonify({'ok': False, 'message': (r.stderr or r.stdout)[-500:]})
        return jsonify({'ok': True, 'filename': name})
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)})

@app.route('/images/<path:filename>')
def images(filename):
    return send_from_directory(IMG, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
