#!/usr/bin/env bash
echo "I2C buses:"
i2cdetect -l || true
echo ""
for b in 1 10 13 14; do
  if [ -e /dev/i2c-$b ]; then
    echo "---- bus $b ----"
    sudo i2cdetect -y $b || true
  fi
done
