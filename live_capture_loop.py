#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hoshinoyakata Allsky External Capture
Ver.5.4 Storage & Interval Fix

Features:
- Configurable save directory: camera.image_dir or storage.save_dir
- Configurable capture interval: camera.live_capture_seconds
- LIVE start/stop support from config/settings.json and data/state.json
- Fallback to data/images if configured save directory is unavailable
"""

from pathlib import Path
from datetime import datetime
import subprocess, time, shutil, json, fcntl, os

BASE = Path(__file__).resolve().parents[1]
DEFAULT_IMG = BASE / "data/images"
LOG = BASE / "data/logs/live_capture.log"
CFG = BASE / "config/settings.json"
STATE = BASE / "data/state.json"
STATUS = BASE / "data/capture_status.json"
LOCK_FILE = BASE / "data/camera.lock"

DEFAULT_IMG.mkdir(parents=True, exist_ok=True)
LOG.parent.mkdir(parents=True, exist_ok=True)

def log(msg):
    line = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "  " + str(msg)
    print(line, flush=True)
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def write_json(path, data):
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    return text not in {
        "false", "0", "off", "no", "n", "stop", "stopped",
        "disabled", "disable", "pause", "paused",
        "停止", "停止中", "止", "止める", "オフ"
    }

def config_live_enabled(settings):
    return to_bool(settings.get("camera", {}).get("auto_capture_enabled", True))

def state_live_enabled():
    state = read_json(STATE, {})
    off_words = {
        "off", "false", "0", "stop", "stopped", "offline",
        "disabled", "pause", "paused", "停止", "停止中", "オフ"
    }
    live = str(state.get("live", "on")).strip().lower()
    camera_status = str(state.get("camera_status", "live")).strip().lower()
    return live not in off_words and camera_status not in off_words

def expand_path(path_text):
    return Path(os.path.expandvars(os.path.expanduser(str(path_text))))

def get_image_dir(settings):
    camera = settings.get("camera", {})
    storage = settings.get("storage", {})
    for value in [
        camera.get("image_dir"),
        camera.get("save_dir"),
        storage.get("image_dir"),
        storage.get("save_dir"),
    ]:
        if value:
            p = expand_path(value)
            try:
                p.mkdir(parents=True, exist_ok=True)
                test = p / ".write_test"
                test.write_text("ok", encoding="utf-8")
                test.unlink(missing_ok=True)
                return p
            except Exception as exc:
                log(f"save dir unavailable: {p} / {exc}")
    DEFAULT_IMG.mkdir(parents=True, exist_ok=True)
    return DEFAULT_IMG

def get_capture_interval(settings):
    camera = settings.get("camera", {})
    storage = settings.get("storage", {})
    for value in [
        camera.get("live_capture_seconds"),
        camera.get("capture_interval_seconds"),
        storage.get("capture_interval_seconds"),
    ]:
        if value is not None:
            try:
                return max(2, min(3600, int(float(value))))
            except Exception:
                pass
    return 5

def get_keep_images(settings):
    camera = settings.get("camera", {})
    storage = settings.get("storage", {})
    for value in [camera.get("keep_images"), storage.get("keep_images")]:
        if value is not None:
            try:
                return max(10, int(value))
            except Exception:
                pass
    return 1200

def save_status(ok, message, filename=None, enabled=True, image_dir=None, interval=None):
    write_json(STATUS, {
        "ok": bool(ok),
        "enabled": bool(enabled),
        "message": str(message),
        "filename": filename,
        "time": datetime.now().strftime("%H:%M:%S"),
        "timestamp": time.time(),
        "version": "5.4 Storage & Interval Fix",
        "image_dir": str(image_dir) if image_dir else None,
        "interval_seconds": interval,
    })

def camtool():
    if shutil.which("rpicam-still"):
        return "rpicam-still"
    if shutil.which("libcamera-still"):
        return "libcamera-still"
    return None

def is_night():
    h = datetime.now().hour
    return h >= 18 or h <= 5

def cleanup_images(image_dir, settings):
    try:
        keep = get_keep_images(settings)
        files = sorted(Path(image_dir).glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in files[keep:]:
            try:
                p.unlink()
            except Exception:
                pass
    except Exception as exc:
        log("cleanup error: " + str(exc))

def build_capture_command(settings, out_path):
    tool = camtool()
    if not tool:
        return None

    camera = settings.get("camera", {})
    width = int(camera.get("width", 3072))
    height = int(camera.get("height", 3072))
    mode = str(camera.get("night_mode", "auto")).lower()

    night_active = (
        mode in ["low", "medium", "mid", "high", "extreme", "night"]
        or (mode == "auto" and is_night())
    )

    if night_active:
        return [
            tool, "-n",
            "--width", str(width),
            "--height", str(height),
            "--shutter", str(int(camera.get("night_exposure_us", 1800000))),
            "--gain", str(int(camera.get("night_gain", 20))),
            "--awbgains", "1.35,1.55",
            "--denoise", "cdn_hq",
            "--timeout", str(int(camera.get("photo_timeout_ms_night", 2500))),
            "-o", str(out_path),
        ]

    return [
        tool, "-n",
        "--width", str(width),
        "--height", str(height),
        "--timeout", str(int(camera.get("photo_timeout_ms_day", 1000))),
        "-o", str(out_path),
    ]

def update_latest_link(image_dir, out_path):
    try:
        latest = Path(image_dir) / "latest.jpg"
        if latest.exists() or latest.is_symlink():
            latest.unlink()
        try:
            latest.symlink_to(out_path.name)
        except Exception:
            shutil.copy2(out_path, latest)
    except Exception:
        pass

def capture_once(settings, image_dir, interval):
    out_path = Path(image_dir) / f"allsky_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    command = build_capture_command(settings, out_path)

    if not command:
        msg = "camera command not found"
        log(msg)
        save_status(False, msg, enabled=True, image_dir=image_dir, interval=interval)
        return

    timeout_seconds = int(settings.get("camera", {}).get("capture_timeout_seconds", 45))

    try:
        with LOCK_FILE.open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            result = subprocess.run(command, text=True, capture_output=True, timeout=timeout_seconds)
            fcntl.flock(lock, fcntl.LOCK_UN)

        if result.returncode == 0 and out_path.exists():
            log("saved " + str(out_path))
            update_latest_link(image_dir, out_path)
            save_status(True, "保存OK", out_path.name, enabled=True, image_dir=image_dir, interval=interval)
            cleanup_images(image_dir, settings)
            return

        msg = (result.stderr or result.stdout or "capture failed")[-500:]
        log("capture failed " + msg)
        save_status(False, msg, enabled=True, image_dir=image_dir, interval=interval)

    except subprocess.TimeoutExpired:
        msg = "capture timeout"
        log(msg)
        save_status(False, msg, enabled=True, image_dir=image_dir, interval=interval)
    except Exception as exc:
        msg = "capture error: " + str(exc)
        log(msg)
        save_status(False, msg, enabled=True, image_dir=image_dir, interval=interval)

def main():
    log("external capture started / Ver.5.4 Storage & Interval Fix")
    last_enabled = None
    last_dir = None
    last_interval = None

    while True:
        settings = read_json(CFG, {})
        enabled = config_live_enabled(settings) and state_live_enabled()
        interval = get_capture_interval(settings)
        image_dir = get_image_dir(settings)

        if image_dir != last_dir:
            log("save dir = " + str(image_dir))
            last_dir = image_dir

        if interval != last_interval:
            log("capture interval = " + str(interval) + " sec")
            last_interval = interval

        if enabled != last_enabled:
            if enabled:
                log("LIVE enabled")
                save_status(True, "LIVE ON", enabled=True, image_dir=image_dir, interval=interval)
            else:
                log("LIVE disabled - capture paused")
                save_status(True, "LIVE停止中", enabled=False, image_dir=image_dir, interval=interval)
            last_enabled = enabled

        if enabled:
            capture_once(settings, image_dir, interval)
            time.sleep(interval)
        else:
            save_status(True, "LIVE停止中", enabled=False, image_dir=image_dir, interval=interval)
            time.sleep(2)

if __name__ == "__main__":
    main()
