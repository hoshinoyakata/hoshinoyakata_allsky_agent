#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hoshinoyakata_allsky_agent_v0_2
全天カメラ ライブ表示・撮影・真円固定表示版

修正点 v0.2:
- ブラウザ表示で円が楕円にならないよう、正方形キャンバスで表示
- 保存画像も正方形ベースに整形
- 全画面表示でも縦横比を維持
"""

from flask import Flask, render_template, Response, send_from_directory, jsonify
from pathlib import Path
from datetime import datetime
import subprocess
import time
import cv2
import numpy as np

APP_DIR = Path(__file__).resolve().parent
CAPTURE_DIR = APP_DIR / "captures"
CAPTURE_DIR.mkdir(exist_ok=True)

app = Flask(__name__)

# カメラ設定
WIDTH = 1456
HEIGHT = 1088
LIVE_SIZE = 900       # 表示・保存用の正方形サイズ
JPEG_QUALITY = 88
CAMERA_INDEX = 0      # USBカメラなら 0。Pi Camera(libcamera)運用なら下の USE_LIBCAMERA=True
USE_LIBCAMERA = False


def make_square_canvas(frame, size=LIVE_SIZE):
    """元画像の縦横比を崩さず、正方形キャンバス中央に配置する。"""
    if frame is None:
        canvas = np.zeros((size, size, 3), dtype=np.uint8)
        cv2.putText(canvas, "NO CAMERA", (size//2-170, size//2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)
        return canvas

    h, w = frame.shape[:2]
    scale = min(size / w, size / h)
    nw, nh = int(w * scale), int(h * scale)
    resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA)

    canvas = np.zeros((size, size, 3), dtype=np.uint8)
    x = (size - nw) // 2
    y = (size - nh) // 2
    canvas[y:y+nh, x:x+nw] = resized
    return canvas


def draw_fisheye_circle(frame):
    """魚眼の外周目安を真円で描く。楕円にはしない。"""
    size = frame.shape[0]
    center = (size // 2, size // 2)
    radius = int(size * 0.47)
    out = frame.copy()
    cv2.circle(out, center, radius, (255, 180, 0), 4)
    return out


def read_usb_frame():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    time.sleep(0.2)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return None
    return frame


def read_libcamera_frame():
    tmp = APP_DIR / "_latest_raw.jpg"
    cmd = [
        "libcamera-still",
        "--width", str(WIDTH),
        "--height", str(HEIGHT),
        "--timeout", "1",
        "--nopreview",
        "-o", str(tmp)
    ]
    try:
        subprocess.run(cmd, check=True, timeout=8, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        frame = cv2.imread(str(tmp))
        return frame
    except Exception:
        return None


def get_frame():
    frame = read_libcamera_frame() if USE_LIBCAMERA else read_usb_frame()
    square = make_square_canvas(frame)
    marked = draw_fisheye_circle(square)
    return marked


def encode_jpeg(frame):
    ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
    if not ok:
        return b""
    return buffer.tobytes()


def mjpeg_stream():
    while True:
        frame = get_frame()
        jpg = encode_jpeg(frame)
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n")
        time.sleep(1.0)


@app.route("/")
def index():
    files = sorted(CAPTURE_DIR.glob("*.jpg"), reverse=True)[:20]
    return render_template("index.html", files=[f.name for f in files])


@app.route("/video_feed")
def video_feed():
    return Response(mjpeg_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/capture")
def capture():
    frame = get_frame()
    filename = "allsky_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
    path = CAPTURE_DIR / filename
    cv2.imwrite(str(path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
    return jsonify({"ok": True, "filename": filename})


@app.route("/captures/<path:filename>")
def captures(filename):
    return send_from_directory(CAPTURE_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
