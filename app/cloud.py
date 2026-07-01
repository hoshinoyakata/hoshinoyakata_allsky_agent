from pathlib import Path
import cv2
import numpy as np

def estimate_cloud_percent(image_path):
    p = Path(image_path)
    if not p.exists():
        return None
    img = cv2.imread(str(p))
    if img is None:
        return None
    small = cv2.resize(img, (480, 270))
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    # 夜空では白っぽく明るい領域を雲候補にする簡易判定
    v = hsv[:, :, 2]
    s = hsv[:, :, 1]
    mask = (v > 80) & (s < 80)
    percent = float(mask.mean() * 100.0)
    return round(percent, 1)
