"""
02_detect_speech_ffmpeg.py
Detect speech intervals by finding SILENCE intervals using ffmpeg silencedetect,
then converting to SPEECH intervals.

Outputs:
  data_index/speech_segments.csv
  data_index/silence_segments.csv
  data_index/vad_audit.csv

Run:
  python scripts/02_detect_speech_ffmpeg.py
"""

from pathlib import Path
import subprocess
import re
import csv

BASE_DIR = Path(__file__).resolve().parents[1]
CLIPS_DIR = BASE_DIR / "data" / "clips"
OUT_DIR = BASE_DIR / "data_index"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Tunable parameters ---
SILENCE_DB = -35        # threshold in dB. If too sensitive, try -30. If missing silence, try -40.
MIN_SILENCE = 0.30      # seconds. Ignore tiny pauses shorter than this.
PAD = 0.05              # seconds. Trim edges slightly to avoid treating breaths as speech boundaries.
MIN_SPEECH = 0.25       # seconds. Drop micro speech segments.

def run(cmd):
    return subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def probe_duration_seconds(mp4_path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(mp4_path)
    ]
    p = run(cmd)
    if p.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {mp4_path.name}:\n{p.stderr}")
    return float(p.stdout.strip())

def detect_silence(mp4_path: Path, silence_db: int, min_silence: float):
    """
    Returns list of (silence_start, silence_end) in seconds.
    """
    cmd = [
        "ffmpeg", "-hide_banner", "-i", str(mp4_path),
        "-af", f"silencedetect=noise={silence_db}dB:d={min_silence}",
        "-f", "null", "-"
    ]
    p = run(cmd)
    if p.returncode != 0:
        # silencedetect logs to stderr even when OK; but nonzero could still happen in some builds
        # We'll still parse stderr if present
        pass

    log = p.stderr

    # Patterns:
    # silence_start: 12.345
    # silence_end: 15.678 | silence_duration: 3.333
    starts = [float(x) for x in re.findall(r"silence_start:\s*([0-9.]+)", log)]
    ends   = [float(x) for x in re.findall(r"silence_end:\s*([0-9.]+)", log)]

    # Pair starts and ends safely
    silences = []
    for s, e in zip(starts, ends):
        if e > s:
            silences.append((s, e))

    # If there's a trailing silence_start without silence_end (silence runs to end), handle it
    if len(starts) > len(ends):
        silences.append((starts[-1], None))

    return silences

def invert_to_speech(silences, dur, pad, min_speech):
    """
    Convert silence intervals to speech intervals across [0, dur].
    silences: list of (s, e) where e can be None meaning end of file.
    """
    # Normalize silences
    norm = []
    for s, e in silences:
        if e is None:
            e = dur
        s = max(0.0, min(s, dur))
        e = max(0.0, min(e, dur))
        if e > s:
            norm.append((s, e))
    norm.sort()

    # Merge overlapping silences
    merged = []
    for s, e in norm:
        if not merged or s > merged[-1][1]:
            merged.append([s, e])
        else:
            merged[-1][1] = max(merged[-1][1], e)

    # Speech is complement of silences
    speech = []
    cur = 0.0
    for s, e in merged:
        if s > cur:
            speech.append([cur, s])
        cur = max(cur, e)
    if cur < dur:
        speech.append([cur, dur])

    # Apply padding and remove tiny segments
    cleaned = []
    for s, e in speech:
        s2 = s + pad
        e2 = e - pad
        if e2 <= s2:
            continue
        if (e2 - s2) >= min_speech:
            cleaned.append([s2, e2])

    return cleaned, [(s, e) for s, e in merged]

def main():
    mp4_files = sorted(CLIPS_DIR.glob("GH*.mp4"))
    if not mp4_files:
        raise SystemExit(f"No GH*.mp4 files found in {CLIPS_DIR}")

    speech_rows = []
    silence_rows = []
    audit_rows = []

    for mp4 in mp4_files:
        file_id = mp4.stem
        dur = probe_duration_seconds(mp4)

        silences = detect_silence(mp4, SILENCE_DB, MIN_SILENCE)
        speech, merged_silences = invert_to_speech(silences, dur, PAD, MIN_SPEECH)

        total_speech = sum(e - s for s, e in speech)
        speech_ratio = (total_speech / dur) if dur else 0

        for s, e in speech:
            speech_rows.append({
                "file": file_id,
                "start_ms": int(round(s * 1000)),
                "end_ms": int(round(e * 1000)),
                "dur_ms": int(round((e - s) * 1000))
            })

        for s, e in merged_silences:
            silence_rows.append({
                "file": file_id,
                "start_ms": int(round(s * 1000)),
                "end_ms": int(round(e * 1000)),
                "dur_ms": int(round((e - s) * 1000))
            })

        audit_rows.append({
            "file": file_id,
            "clip_dur_s": round(dur, 2),
            "speech_dur_s": round(total_speech, 2),
            "speech_ratio": round(speech_ratio, 3),
            "n_speech_segments": len(speech),
            "n_silence_segments": len(merged_silences),
            "silence_db": SILENCE_DB,
            "min_silence_s": MIN_SILENCE
        })

    speech_csv = OUT_DIR / "speech_segments.csv"
    silence_csv = OUT_DIR / "silence_segments.csv"
    audit_csv = OUT_DIR / "vad_audit.csv"

    with speech_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file","start_ms","end_ms","dur_ms"])
        w.writeheader()
        w.writerows(speech_rows)

    with silence_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file","start_ms","end_ms","dur_ms"])
        w.writeheader()
        w.writerows(silence_rows)

    with audit_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["file","clip_dur_s","speech_dur_s","speech_ratio","n_speech_segments","n_silence_segments","silence_db","min_silence_s"]
        )
        w.writeheader()
        w.writerows(audit_rows)

    print("Wrote:")
    print(" ", speech_csv)
    print(" ", silence_csv)
    print(" ", audit_csv)

if __name__ == "__main__":
    main()