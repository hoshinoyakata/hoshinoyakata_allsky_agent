#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import subprocess
import time
import shutil
import json
import fcntl

BASE = Path(__file__).resolve().parents[1]
IMG = BASE / "data/images"
LOG = BASE / "data/logs/live_capture.log"
CFG = BASE / "config/settings.json"
STATUS = BASE / "data/capture_status.json"
LOCK_FILE = BASE / "data/camera.lock"

IMG.mkdir(parents=True, exist_ok=True)
LOG.parent.mkdir(parents=True, exist_ok=True)

def log(msg):
    line = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "  " + str(msg)
    print(line, flush=True)
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def save_status(ok, message, filename=None, enabled=True):
    try:
        STATUS.write_text(json.dumps({
            "ok": bool(ok),
            "enabled": bool(enabled),
            "message": str(message),
            "filename": filename,
            "time": datetime.now().strftime("%H:%M:%S"),
            "timestamp": time.time()
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def load_cfg():
    try:
        return json.loads(CFG.read_text(encoding="utf-8"))
    except Exception:
        return {}

def camtool():
    if shutil.which("rpicam-still"):
        return "rpicam-still"
    if shutil.which("libcamera-still"):
        return "libcamera-still"
    return None

def is_night():
    h = datetime.now().hour
    return h >= 18 or h <= 5

def build_cmd(out, cfg):
    tool = camtool()
    if not tool:
        return None
    cam = cfg.get("camera", {})
    width = int(cam.get("width", 3072))
    height = int(cam.get("height", 3072))
    mode = cam.get("night_mode", "auto")

    if mode in ["low", "medium", "high", "extreme", "night"] or (mode == "auto" and is_night()):
        return [
            tool, "-n",
            "--width", str(width),
            "--height", str(height),
            "--shutter", str(int(cam.get("night_exposure_us", 1800000))),
            "--gain", str(int(cam.get("night_gain", 20))),
            "--awbgains", "1.35,1.55",
            "--denoise", "cdn_hq",
            "--timeout", str(int(cam.get("photo_timeout_ms_night", 2500))),
            "-o", str(out)
        ]

    return [
        tool, "-n",
        "--width", str(width),
        "--height", str(height),
        "--timeout", str(int(cam.get("photo_timeout_ms_day", 1000))),
        "-o", str(out)
    ]

def cleanup(cfg):
    keep = int(cfg.get("camera", {}).get("keep_images", 1200))
    files = sorted(IMG.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in files[keep:]:
        try:
            p.unlink()
        except Exception:
            pass

def capture_once(cfg):
    out = IMG / f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    cmd = build_cmd(out, cfg)
    if not cmd:
        msg = "camera command not found"
        log(msg)
        save_status(False, msg)
        return

    timeout_s = int(cfg.get("camera", {}).get("capture_timeout_seconds", 40))
    try:
        with LOCK_FILE.open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            r = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout_s)
            fcntl.flock(lock, fcntl.LOCK_UN)
    except subprocess.TimeoutExpired:
        msg = "capture timeout"
        log(msg)
        save_status(False, msg)
        return
    except Exception as e:
        msg = "capture exception: " + str(e)
        log(msg)
        save_status(False, msg)
        return

    if r.returncode == 0 and out.exists():
        cleanup(cfg)
        msg = "saved " + out.name
        log(msg)
        save_status(True, "保存OK", out.name, enabled=True)
    else:
        msg = "capture failed " + (r.stderr or r.stdout or "")[-300:]
        log(msg)
        save_status(False, msg)

def main():
    log("external capture started / live stop supported")
    last_enabled = None
    while True:
        cfg = load_cfg()
        cam = cfg.get("camera", {})
        enabled = bool(cam.get("auto_capture_enabled", True))
        interval = max(2, int(cam.get("live_capture_seconds", 5)))

        if enabled != last_enabled:
            if enabled:
                log("LIVE enabled")
                save_status(True, "LIVE ON", enabled=True)
            else:
                log("LIVE disabled - capture paused")
                save_status(True, "LIVE停止中", enabled=False)
            last_enabled = enabled

        if enabled:
            capture_once(cfg)
            time.sleep(interval)
        else:
            # LIVE停止中は撮影せず、状態だけ更新。これで直近キャプチャ時刻が止まる。
            save_status(True, "LIVE停止中", enabled=False)
            time.sleep(2)

if __name__ == "__main__":
    main()
