#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import json, shutil, subprocess, time, os, sys

BASE = Path(__file__).resolve().parents[1]
CONFIG = BASE / "config/settings.json"
IMG = BASE / "data/images"
LOG = BASE / "data/logs/live_capture.log"
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

def cfg():
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception as e:
        log("config read error: " + str(e))
        return {}

def has(cmd):
    return shutil.which(cmd) is not None

def camtool(kind):
    if has("rpicam-" + kind):
        return "rpicam-" + kind
    if has("libcamera-" + kind):
        return "libcamera-" + kind
    return ""

def is_night():
    h = datetime.now().hour
    return h >= 18 or h <= 5

def still_cmd(out):
    s = cfg()
    c = s.get("camera", {})
    tool = camtool("still")
    if not tool:
        return None
    w = int(c.get("width", 3072))
    h = int(c.get("height", 3072))
    mode = c.get("night_mode", "auto")
    night_active = is_night() if mode == "auto" else mode in ["low", "medium", "high", "extreme", "night"]

    if mode == "day" or not night_active:
        return [
            tool, "-n",
            "--width", str(w),
            "--height", str(h),
            "--timeout", str(int(c.get("photo_timeout_ms_day", 1000))),
            "-o", str(out)
        ]

    presets = {
        "low": (500000, 8, 1000),
        "medium": (1000000, 14, 1500),
        "high": (1800000, 20, 2500),
        "extreme": (3000000, 26, 3500),
        "auto": (int(c.get("night_exposure_us", 1800000)), int(c.get("night_gain", 20)), int(c.get("photo_timeout_ms_night", 2500))),
        "night": (int(c.get("night_exposure_us", 1800000)), int(c.get("night_gain", 20)), int(c.get("photo_timeout_ms_night", 2500))),
    }
    shutter, gain, timeout_ms = presets.get(mode, presets["auto"])
    return [
        tool, "-n",
        "--width", str(w),
        "--height", str(h),
        "--shutter", str(shutter),
        "--gain", str(gain),
        "--awbgains", "1.35,1.55",
        "--denoise", "cdn_hq",
        "--timeout", str(timeout_ms),
        "-o", str(out)
    ]

def cleanup():
    s = cfg()
    keep = int(s.get("camera", {}).get("keep_images", 1200))
    files = sorted(IMG.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in files[keep:]:
        try:
            p.unlink()
        except Exception:
            pass

def capture_once():
    out = IMG / f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    cmd = still_cmd(out)
    if not cmd:
        log("camera command not found")
        return False
    timeout_s = int(cfg().get("camera", {}).get("capture_timeout_seconds", 30))
    try:
        r = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout_s)
        if r.returncode == 0 and out.exists():
            log("saved " + out.name)
            cleanup()
            return True
        log("capture failed: " + (r.stderr or r.stdout or "unknown")[-500:])
        return False
    except subprocess.TimeoutExpired:
        log("capture timeout")
        return False
    except Exception as e:
        log("capture exception: " + str(e))
        return False

def main():
    log("external live capture started")
    while True:
        s = cfg()
        c = s.get("camera", {})
        enabled = bool(c.get("auto_capture_enabled", True))
        interval = max(2, int(c.get("live_capture_seconds", 5)))
        if enabled:
            capture_once()
        time.sleep(interval)

if __name__ == "__main__":
    main()
