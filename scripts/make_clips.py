import csv
import subprocess
from pathlib import Path
import re

# -----------------------------
# Paths (works no matter where you run from)
# -----------------------------
BASE_DIR = Path(__file__).resolve().parents[1]  # twiteach-multi/
CSV_PATH = BASE_DIR / "data_index" / "video_index.csv"
RAW_DIR = BASE_DIR / "data" / "raw_videos"
OUT_DIR = BASE_DIR / "data" / "clips"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Helpers
# -----------------------------
def run(cmd):
    # capture output so ffmpeg doesn't spam the terminal
    return subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def parse_hhmmss(t: str) -> float:
    """
    Accepts hh:mm:ss or mm:ss or ss
    """
    t = (t or "").strip()
    if not t:
        raise ValueError("Empty time string")

    parts = t.split(":")
    if len(parts) == 1:
        return float(parts[0])
    if len(parts) == 2:
        mm, ss = parts
        return float(mm) * 60 + float(ss)
    if len(parts) == 3:
        hh, mm, ss = parts
        return float(hh) * 3600 + float(mm) * 60 + float(ss)
    raise ValueError(f"Bad time format: {t}")

def extract_video_id(url: str) -> str:
    """
    Tries to extract YouTube video id from a watch URL.
    """
    if not url:
        return ""
    m = re.search(r"[?&]v=([^&]+)", url)
    return m.group(1) if m else ""

def ffprobe_duration(path: Path) -> float:
    """
    Returns duration in seconds, or -1 if unknown.
    """
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1",
        str(path)
    ]
    p = run(cmd)
    if p.returncode != 0:
        return -1
    try:
        return float(p.stdout.strip())
    except Exception:
        return -1

def is_good_output(path: Path, expected_dur: float) -> bool:
    """
    Basic validation: file exists, not tiny, and ffprobe reports a duration close to expected.
    """
    if not path.exists():
        return False
    if path.stat().st_size < 50_000:  # 50KB (tiny = probably broken)
        return False
    dur = ffprobe_duration(path)
    if dur <= 0:
        return False
    # allow a little slack (+/- 1.5s)
    return abs(dur - expected_dur) <= 1.5 or dur >= expected_dur - 1.5

# -----------------------------
# Main
# -----------------------------
def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Cannot find CSV at: {CSV_PATH}")

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} rows from {CSV_PATH}")

    failed = []

    for r in rows:
        clip_id = r.get("clip_id", "").strip()
        if not clip_id:
            continue

        # Determine start/end seconds
        if "start_sec" in r and "end_sec" in r and r["start_sec"].strip() and r["end_sec"].strip():
            start_sec = float(r["start_sec"])
            end_sec = float(r["end_sec"])
        else:
            start_sec = parse_hhmmss(r.get("start_time", ""))
            end_sec = parse_hhmmss(r.get("end_time", ""))

        duration = max(0.01, end_sec - start_sec)

        # Determine source video path
        local_video_path = (r.get("local_video_path") or "").strip()
        if local_video_path:
            video_path = (BASE_DIR / local_video_path).resolve() if not Path(local_video_path).is_absolute() else Path(local_video_path)
        else:
            vid = r.get("video_id", "").strip() or extract_video_id(r.get("youtube_url", ""))
            video_path = RAW_DIR / f"{vid}.mp4"

        out_path = OUT_DIR / f"{clip_id}.mp4"

        # Skip if already good
        if is_good_output(out_path, duration):
            print(f"[OK] {clip_id} already exists and looks valid.")
            continue

        # If exists but bad, delete and recreate
        if out_path.exists():
            try:
                out_path.unlink()
            except Exception:
                pass

        if not video_path.exists():
            print(f"[SKIP] Missing source video for {clip_id}: {video_path}")
            failed.append((clip_id, "missing source video"))
            continue

        # Quick sanity check: does the source video reach the needed timestamp?
        src_dur = ffprobe_duration(video_path)
        if src_dur > 0 and start_sec > src_dur:
            msg = f"start_sec ({start_sec}) beyond source duration ({src_dur:.1f}). Source file likely incomplete."
            print(f"[FAIL] {clip_id}: {msg}")
            failed.append((clip_id, msg))
            continue

        print(f"\n=== Cutting {clip_id} from {video_path.name}: {start_sec:.2f}s -> {end_sec:.2f}s ({duration:.2f}s) ===")

        # More stable cutting on messy MP4s: place -ss AFTER -i (slower but reliable)
        cmd = [
            "ffmpeg", "-y",
            "-hide_banner", "-loglevel", "error", "-nostats",
            "-fflags", "+genpts",
            "-err_detect", "ignore_err",
            "-i", str(video_path),
            "-ss", str(start_sec),
            "-t", str(duration),
            "-c:v", "libx264", "-crf", "23", "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(out_path)
        ]

        p = run(cmd)
        if p.returncode != 0:
            msg = p.stderr.strip().splitlines()[-1] if p.stderr.strip() else "ffmpeg error"
            print(f"[FAIL] {clip_id}: {msg}")
            failed.append((clip_id, msg))
            continue

        # Validate output
        if not is_good_output(out_path, duration):
            msg = "output created but failed validation (likely source corruption at that timestamp)"
            print(f"[FAIL] {clip_id}: {msg}")
            try:
                out_path.unlink()
            except Exception:
                pass
            failed.append((clip_id, msg))
            continue

        print(f"[DONE] {clip_id} -> {out_path}")

    print("\n=== SUMMARY ===")
    if failed:
        print(f"{len(failed)} clips failed:")
        for cid, reason in failed:
            print(f"  - {cid}: {reason}")
        print("\nMost common fix: re-download the raw video(s) that fail, because the local MP4 is truncated/corrupted.")
    else:
        print("All clips created successfully.")

if __name__ == "__main__":
    main()
