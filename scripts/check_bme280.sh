#!/usr/bin/env bash
cd "$(dirname "$0")/.."
source venv/bin/activate || true
python - <<'PY'
try:
    from bme280 import BME280
    import inspect
    print(inspect.signature(BME280))
except Exception as e:
    print(e)
PY
i2cdetect -l || true
for b in 1 10 13 14; do
  [ -e /dev/i2c-$b ] && echo "---- bus $b ----" && sudo i2cdetect -y $b || true
done
