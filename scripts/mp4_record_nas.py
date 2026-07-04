#!/usr/bin/env python3
# Hoshinoyakata Allsky Ver5.6 - NAS MP4 recorder
from __future__ import annotations
import argparse, datetime as dt, json, os, shutil, subprocess, sys, time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
NAS_BASE = Path(os.environ.get("HOSHI_NAS_BASE", "/mnt/hoshinoyakata_nas/全天カメラ"))
VIDEO_DIR = Path(os.environ.get("HOSHI_VIDEO_DIR", str(NAS_BASE / "MP4動画")))
IMAGE_DIRS = [NAS_BASE, BASE / "data" / "images"]
STATUS_FILE = BASE / "data" / "mp4_record_status.json"

def write_status(**kw):
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    base = {"ok": True, "recording": False, "message": "idle", "updated": dt.datetime.now().isoformat(timespec="seconds")}
    base.update(kw)
    STATUS_FILE.write_text(json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8")

def latest_images(limit: int = 300):
    items = []
    for d in IMAGE_DIRS:
        if not d.exists():
            continue
        for p in d.glob("*.jpg"):
            if p.name.startswith("allsky_") or p.name == "latest.jpg":
                try:
                    items.append((p.stat().st_mtime, p))
                except FileNotFoundError:
                    pass
    # unique paths, newest first
    seen, out = set(), []
    for _, p in sorted(items, reverse=True):
        if p.resolve() not in seen and p.name != "latest.jpg":
            seen.add(p.resolve()); out.append(p)
            if len(out) >= limit: break
    return list(reversed(out))

def have_ffmpeg():
    return shutil.which("ffmpeg") is not None

def make_video(seconds: int, fps: int, output: Path):
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    end = time.time() + seconds
    frames = []
    frame_interval = 1.0 / max(1, fps)
    temp_dir = BASE / "data" / "mp4_frames_tmp"
    if temp_dir.exists(): shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    i = 0
    write_status(recording=True, message="recording", seconds=seconds, fps=fps, output=str(output))
    while time.time() < end:
        imgs = latest_images(1)
        if imgs:
            src = imgs[-1]
            dst = temp_dir / f"frame_{i:05d}.jpg"
            try:
                shutil.copy2(src, dst); frames.append(dst); i += 1
            except Exception as e:
                write_status(recording=True, message=f"frame copy error: {e}", output=str(output))
        time.sleep(frame_interval)
    if not frames:
        raise RuntimeError("録画用の静止画が見つかりませんでした")
    if not have_ffmpeg():
        raise RuntimeError("ffmpeg が見つかりません。sudo apt install -y ffmpeg を実行してください")
    cmd = ["ffmpeg", "-y", "-framerate", str(fps), "-i", str(temp_dir / "frame_%05d.jpg"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:])
    shutil.rmtree(temp_dir, ignore_errors=True)
    write_status(recording=False, message="saved", output=str(output), bytes=output.stat().st_size)
    return output

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=30)
    ap.add_argument("--fps", type=int, default=2)
    args = ap.parse_args()
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = VIDEO_DIR / f"allsky_{ts}.mp4"
    print(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] MP4 recording start: {args.seconds}s {args.fps}fps -> {out}", flush=True)
    try:
        make_video(args.seconds, args.fps, out)
        print(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] MP4 saved: {out} ({out.stat().st_size} bytes)", flush=True)
    except Exception as e:
        write_status(ok=False, recording=False, message=str(e), output=str(out))
        print(f"MP4 ERROR: {e}", file=sys.stderr)
        return 1
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
