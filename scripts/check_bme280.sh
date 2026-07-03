#!/usr/bin/env bash
cd ~/hoshinoyakata_allsky_agent_real_v2
source venv/bin/activate
python - <<'BMEPY'
from bme280 import BME280
from smbus2 import SMBus
bus=SMBus(1); bme=BME280(i2c_dev=bus)
raw=float(bme.get_pressure()); temp=float(bme.get_temperature()); hum=float(bme.get_humidity())
station=raw*1.3332239 if raw<850 else raw
sea=station/((1-108/44330.0)**5.255)
print("Temp =",round(temp,1)); print("Hum =",round(hum,1)); print("Raw pressure =",round(raw,2)); print("Station hPa =",round(station,1)); print("Sea level hPa altitude108m =",round(sea,1))
BMEPY
