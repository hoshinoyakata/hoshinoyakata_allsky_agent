#!/usr/bin/env bash
cd ~/hoshinoyakata_allsky_agent_real_v2
source venv/bin/activate
python - <<'PY'
from bme280 import BME280
from smbus2 import SMBus
import json
s=json.load(open('config/settings.json'))
b=s.get('bme280',{})
sensor=BME280(i2c_dev=SMBus(int(b.get('bus',1))))
raw=float(sensor.get_pressure())
temp=float(sensor.get_temperature())
hum=float(sensor.get_humidity())
station=raw*1.3332239 if raw<850 else raw
alt=float(b.get('altitude_m',108))
sea=station/((1-alt/44330.0)**5.255)
off=float(b.get('pressure_offset_hpa',38.0))
print('Temp',round(temp,1))
print('Hum',round(hum,1))
print('Raw',round(raw,2))
print('Sea(no offset)',round(sea,1))
print('Offset',off)
print('Display',round(sea+off,1))
PY
