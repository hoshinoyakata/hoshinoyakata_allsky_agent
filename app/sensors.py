import random

def read_bme280():
    # 実機BME280が未設定でも画面が動くよう、失敗時はデモ値を返します。
    try:
        # 次版で実センサー読取を本格実装。配線: 3.3V, GND, SDA(GPIO2), SCL(GPIO3)
        raise RuntimeError("BME280 driver not configured")
    except Exception:
        return {
            "temperature": round(22.0 + random.uniform(-1, 1), 1),
            "humidity": round(55.0 + random.uniform(-5, 5), 1),
            "pressure": round(1013.0 + random.uniform(-3, 3), 1),
            "source": "demo"
        }
