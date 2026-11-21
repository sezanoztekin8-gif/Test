#!/usr/bin/env python3
"""Assembles grids (low-fidelity) and writes manifest.json."""

import argparse
import json
import math
import re
import sys
from pathlib import Path


def detect_platform(url: str) -> str:
    if re.search(r'instagram\.com|instagr\.am', url):
        return 'instagram'
    if re.search(r'tiktok\.com|vm\.tiktok\.com', url):
        return 'tiktok'
    if re.search(r'youtube\.com|youtu\.be', url):
        return 'youtube'
    if re.search(r'twitter\.com|x\.com|twimg\.com', url):
        return 'twitter'
    return 'other'


def find_transcript_for_timestamp(t: float, interval: float, segments: list):
    """Return (text, [start, end]) for transcript segments overlapping [t, t+interval)."""
    window_end = t + interval
    matching = [s for s in segments if s['start'] < window_end and s['end'] > t]
    if not matching and segments:
        closest = min(segments, key=lambda s: abs(s['start'] - t))
        return closest['text'].strip(), [closest['start'], closest['end']]
    if matching:
        text = ' '.join(s['text'].strip() for s in matching)
        return text, [matching[0]['start'], matching[-1]['end']]
    return '', []


def create_grid(frame_paths: list, labels: list, out_path: str) -> bool:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Warning: Pillow not available, skipping grid creation", file=sys.stderr)
        return False

    n = len(frame_paths)
    if n <= 0:
        return False
    cols = 2 if n >= 4 else n
    rows = math.ceil(n / cols)

    max_cell_dim = 512
    images = []
    for fp in frame_paths:
        try:
            img = Image.open(fp).convert('RGB')
            img.thumbnail((max_cell_dim, max_cell_dim), Image.LANCZOS)
            images.append(img)
        except Exception as e:
            print(f"Warning: could not open {fp}: {e}", file=sys.stderr)

    if not images:
        return False

    cell_w = max(img.width for img in images)
    cell_h = max(img.height for img in images)
    gutter = 4

    grid_w = cols * cell_w + (cols - 1) * gutter
    grid_h = rows * cell_h + (rows - 1) * gutter

    grid = Image.new('RGB', (grid_w, grid_h), (20, 20, 20))
    draw = ImageDraw.Draw(grid)

    font = None
    for font_path in (
        "/System/Library/Fonts/Helvetica.ttc",                              # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",             # Debian/Ubuntu
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",                      # Fedora/Arch
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",     # Liberation
        "C:\\Windows\\Fonts\\arialbd.ttf",                                  # Windows
    ):
        try:
            font = ImageFont.truetype(font_path, 16)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    for idx, (img, label) in enumerate(zip(images, labels)):
        row = idx // cols
        col = idx % cols
        x = col * (cell_w + gutter)
        y = row * (cell_h + gutter)
        offset_x = (cell_w - img.width) // 2
        offset_y = (cell_h - img.height) // 2
        grid.paste(img, (x + offset_x, y + offset_y))
        # Timestamp label with shadow for readability
        lx, ly = x + offset_x + 6, y + offset_y + 4
        draw.text((lx + 1, ly + 1), label, fill=(0, 0, 0), font=font)
        draw.text((lx, ly), label, fill=(255, 220, 0), font=font)

    grid.save(out_path, 'JPEG', quality=70, optimize=True)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--url', required=True)
    parser.add_argument('--fidelity', default='high', choices=['high', 'low'])
    parser.add_argument('--grid-size', type=int, default=4)
    parser.add_argument('--max-frames', type=int, default=20)
    parser.add_argument('--interval', type=float, default=None)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    frames_dir = out_dir / 'frames'
    grids_dir = out_dir / 'grids'
    grids_dir.mkdir(exist_ok=True)

    # Duration
    duration_file = out_dir / 'duration.txt'
    duration = float(duration_file.read_text().strip()) if duration_file.exists() else 0.0

    # Compute interval
    if args.interval:
        interval = float(args.interval)
    else:
        if duration < 30:
            interval = 2.0
        elif duration <= 60:
            interval = 5.0
        else:
            interval = math.ceil(duration / 15)

    count = int(duration / interval) + 1
    if count > args.max_frames and args.max_frames > 0:
        interval = math.ceil(duration / args.max_frames)

    # Download method
    dl_file = out_dir / 'download_method.txt'
    downloaded_via = dl_file.read_text().strip() if dl_file.exists() else 'unknown'

    platform = detect_platform(args.url)

    # Transcript
    transcript_file = out_dir / 'transcript.json'
    transcript_data = {}
    segments = []
    if transcript_file.exists():
        try:
            transcript_data = json.loads(transcript_file.read_text())
            segments = transcript_data.get('segments', [])
            if transcript_data.get('error'):
                transcript_data = {}
                segments = []
        except Exception:
            pass

    # Frames
    frame_files = sorted(frames_dir.glob('*.jpg'))
    frames = []
    for i, frame_file in enumerate(frame_files):
        t = round(i * interval, 2)
        transcript_text, transcript_t = find_transcript_for_timestamp(t, interval, segments)
        frames.append({
            'index': i + 1,
            't_sec': t,
            'image': str(frame_file.relative_to(out_dir)),
            'image_path': str(frame_file.resolve()),
            'transcript': transcript_text,
            'transcript_t': transcript_t,
        })

    # Grids for low fidelity
    grids = []
    if args.fidelity == 'low' and frames:
        gs = max(1, min(args.grid_size, 4))
        for gi, chunk_start in enumerate(range(0, len(frames), gs)):
            chunk = frames[chunk_start:chunk_start + gs]
            frame_paths = [str(out_dir / f['image']) for f in chunk]
            labels = [
                f"{int(f['t_sec']//60):02d}:{int(f['t_sec']%60):02d}"
                for f in chunk
            ]
            grid_path = grids_dir / f'grid_{gi+1:04d}.jpg'
            ok = create_grid(frame_paths, labels, str(grid_path))
            if ok:
                grids.append({
                    'index': gi + 1,
                    'image': str(grid_path.relative_to(out_dir)),
                    'image_path': str(grid_path.resolve()),
                    'frames': [f['index'] for f in chunk],
                    't_range': [chunk[0]['t_sec'], chunk[-1]['t_sec']],
                })

    manifest = {
        'source': {
            'url': args.url,
            'platform': platform,
            'duration_sec': round(duration, 2),
            'downloaded_via': downloaded_via,
        },
        'extraction': {
            'interval_sec': interval,
            'frame_count': len(frames),
            'fidelity': args.fidelity,
            'grid_size': args.grid_size if args.fidelity == 'low' else None,
        },
        'frames': frames,
        'grids': grids,
        'transcript': {
            'language': transcript_data.get('language', ''),
            'text': transcript_data.get('text', ''),
            'segments': segments,
        } if transcript_data else None,
    }

    manifest_path = out_dir / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"Manifest written: {manifest_path}", file=sys.stderr)


if __name__ == '__main__':
    main()
