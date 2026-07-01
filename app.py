from __future__ import annotations

import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, redirect, render_template, send_file, url_for

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
CAPTURES = DATA / "captures"
VIDEOS = DATA / "videos"
LIVE = DATA / "live.jpg"
CAPTURES.mkdir(parents=True, exist_ok=True)
VIDEOS.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
lock = threading.Lock()
last_error = ""
last_capture_time = "-"


def have_command(name: str) -> bool:
    return subprocess.run(["bash", "-lc", f"command -v {name} >/dev/null 2>&1"]).returncode == 0


def capture_jpeg(path: Path, width: int = 1200, height: int = 1200, timeout: int = 8) -> tuple[bool, str]:
    # Raspberry Pi OS Bookworm uses rpicam-still. Bullseye sometimes uses libcamera-still.
    cmd_name = "rpicam-still" if have_command("rpicam-still") else "libcamera-still"
    if not have_command(cmd_name):
        return False, "rpicam-still/libcamera-still not found"
    cmd = [cmd_name, "-n", "-t", "1", "--width", str(width), "--height", str(height), "-o", str(path)]
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, text=True)
        if p.returncode != 0:
            return False, p.stderr[-500:] or f"{cmd_name} failed"
        return True, "ok"
    except Exception as e:
        return False, str(e)


def live_loop() -> None:
    global last_error, last_capture_time
    while True:
        ok, msg = capture_jpeg(LIVE, width=1200, height=1200)
        with lock:
            last_error = "" if ok else msg
            if ok:
                last_capture_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(2)


@app.route("/")
def index():
    images = sorted(CAPTURES.glob("*.jpg"), reverse=True)[:8]
    return render_template("index.html", images=[p.name for p in images])


@app.route("/image")
def image():
    if LIVE.exists():
        return send_file(LIVE, mimetype="image/jpeg", max_age=0)
    # tiny fallback SVG when no image yet
    return Response("<svg xmlns='http://www.w3.org/2000/svg' width='800' height='800'><rect width='100%' height='100%' fill='#020712'/><text x='50%' y='50%' fill='white' text-anchor='middle' font-size='34'>Waiting for camera...</text></svg>", mimetype="image/svg+xml")


@app.route("/capture", methods=["POST"])
def capture():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = CAPTURES / f"allsky_{ts}.jpg"
    ok, msg = capture_jpeg(out, width=1600, height=1600)
    return jsonify({"ok": ok, "file": out.name if ok else "", "message": msg})


@app.route("/record10", methods=["POST"])
def record10():
    # Basic 10 second MP4 recording. It can fail if rpicam-vid is unavailable.
    cmd_name = "rpicam-vid" if have_command("rpicam-vid") else "libcamera-vid"
    if not have_command(cmd_name):
        return jsonify({"ok": False, "message": "rpicam-vid/libcamera-vid not found"})
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = VIDEOS / f"allsky_{ts}.h264"
    cmd = [cmd_name, "-n", "-t", "10000", "--width", "1200", "--height", "1200", "-o", str(out)]
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15, text=True)
        return jsonify({"ok": p.returncode == 0, "file": out.name, "message": "saved" if p.returncode == 0 else p.stderr[-500:]})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})


@app.route("/status")
def status():
    with lock:
        err = last_error
        ts = last_capture_time
    return jsonify({
        "camera": "OK" if not err else "ERROR",
        "error": err,
        "last_image": ts,
        "captures": len(list(CAPTURES.glob("*.jpg"))),
        "videos": len(list(VIDEOS.glob("*.h264"))),
    })


@app.route("/captures/<name>")
def capture_file(name: str):
    path = CAPTURES / name
    if path.exists():
        return send_file(path, mimetype="image/jpeg")
    return "not found", 404


if __name__ == "__main__":
    threading.Thread(target=live_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
