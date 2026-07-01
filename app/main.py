from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, send_file, url_for
from camera import capture_still, latest_image, list_recent
from sensors import read_bme280
from moon import moon_info
from cloud import estimate_cloud_percent

BASE = Path(__file__).resolve().parents[1]
app = Flask(__name__, template_folder=str(BASE / "web" / "templates"), static_folder=str(BASE / "web" / "static"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def status():
    latest = latest_image()
    cloud = estimate_cloud_percent(latest)
    return jsonify({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sensor": read_bme280(),
        "moon": moon_info(),
        "cloud_percent": cloud,
        "sqm": "未接続",
        "ai_status": "監視中",
        "condition": "観測良好" if cloud is not None and cloud < 35 else "雲あり",
        "latest_url": "/image/latest.jpg"
    })

@app.route("/api/capture", methods=["POST", "GET"])
def capture():
    p = capture_still()
    return jsonify({"ok": True, "file": p.name, "url": f"/image/{p.name}"})

@app.route("/api/recent")
def recent():
    return jsonify([{"name": p.name, "url": f"/image/{p.name}"} for p in list_recent()])

@app.route("/image/latest.jpg")
def img_latest():
    return send_file(latest_image(), mimetype="image/jpeg")

@app.route("/image/<name>")
def img(name):
    p = BASE / "data" / "images" / name
    if not p.exists():
        p = latest_image()
    return send_file(p, mimetype="image/jpeg")

@app.route("/api/record", methods=["POST", "GET"])
def record():
    return jsonify({"ok": False, "message": "MP4録画は次版で実機カメラ設定後に有効化します"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
