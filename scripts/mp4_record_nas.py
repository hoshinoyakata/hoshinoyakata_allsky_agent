#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

DEFAULT_NAS = Path('/mnt/hoshinoyakata_nas/全天カメラ')
DEFAULT_SOURCE = DEFAULT_NAS / 'latest.jpg'
DEFAULT_VIDEO_DIR = DEFAULT_NAS / 'MP4動画'
DEFAULT_LOG_DIR = DEFAULT_NAS / 'システムログ'


def log(msg: str) -> None:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{ts}] {msg}', flush=True)
    try:
        DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)
        with (DEFAULT_LOG_DIR / 'mp4_record.log').open('a', encoding='utf-8') as f:
            f.write(f'[{ts}] {msg}\n')
    except Exception:
        pass


def main() -> int:
    ap = argparse.ArgumentParser(description='星の館 全天カメラ NAS MP4録画')
    ap.add_argument('--seconds', type=int, default=30, help='録画秒数')
    ap.add_argument('--fps', type=int, default=2, help='MP4のフレームレート')
    ap.add_argument('--source', default=str(DEFAULT_SOURCE), help='latest.jpg の場所')
    ap.add_argument('--outdir', default=str(DEFAULT_VIDEO_DIR), help='MP4保存先')
    args = ap.parse_args()

    source = Path(args.source)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if not source.exists():
        log(f'ERROR: source not found: {source}')
        return 2
    if shutil.which('ffmpeg') is None:
        log('ERROR: ffmpeg not installed')
        return 3

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    work = Path('/tmp') / f'hoshinoyakata_mp4_{stamp}'
    work.mkdir(parents=True, exist_ok=True)
    output = outdir / f'allsky_{stamp}.mp4'

    frames = max(1, args.seconds * args.fps)
    interval = 1.0 / max(1, args.fps)
    log(f'MP4 recording start: {args.seconds}s {args.fps}fps -> {output}')

    last_size = -1
    for i in range(frames):
        frame = work / f'frame_{i:05d}.jpg'
        try:
            shutil.copy2(source, frame)
            size = frame.stat().st_size
            if size != last_size:
                last_size = size
        except Exception as e:
            log(f'WARN: copy failed: {e}')
        time.sleep(interval)

    cmd = [
        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
        '-framerate', str(args.fps),
        '-i', str(work / 'frame_%05d.jpg'),
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
        str(output)
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        log(f'ERROR: ffmpeg failed: {e}')
        return 4
    finally:
        shutil.rmtree(work, ignore_errors=True)

    log(f'MP4 saved: {output} ({output.stat().st_size} bytes)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
