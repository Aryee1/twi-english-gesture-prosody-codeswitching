"""
05_extract_pitch.py (REVISED - extracts WAV first, then runs Praat)
"""

from pathlib import Path
import subprocess
import csv

BASE_DIR  = Path(__file__).resolve().parents[1]
CLIPS_DIR = BASE_DIR / "data" / "clips"
OUT_DIR   = BASE_DIR / "data_index"
TEMP_DIR  = BASE_DIR / "data_index" / "temp_wav"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ---- SET THIS TO YOUR PRAAT EXECUTABLE PATH ----
PRAAT_EXE = r"C:\Program Files\Praat\Praat.exe"

F0_MIN    = 75    # Hz - lower bound for F0 tracking
F0_MAX    = 300   # Hz - upper bound for F0 tracking
TIME_STEP = 0.01  # seconds (10ms frames)

PRAAT_SCRIPT_TEMPLATE = """\
input_path$ = "{input_path}"
output_path$ = "{output_path}"

sound = Read from file: input_path$
pitch = To Pitch (ac): {time_step}, {f0_min}, 15, "no", 0.03, 0.45, 0.01, 0.35, 0.14, {f0_max}

deleteFile: output_path$
appendFileLine: output_path$, "time_ms,pitch_hz"

n = Get number of frames
for i from 1 to n
    t = Get time from frame number: i
    f = Get value in frame: i, "Hertz"
    if f <> undefined
        appendFileLine: output_path$, round(t * 1000), ",", f
    endif
endfor

Remove
selectObject: sound
Remove
"""

def extract_wav(mp4_path: Path, wav_path: Path) -> bool:
    """Use ffmpeg to extract mono 16kHz WAV from MP4."""
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(mp4_path),
        "-ac", "1",          # mono
        "-ar", "16000",      # 16kHz sample rate
        "-vn",               # no video
        str(wav_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [ERROR] ffmpeg WAV extraction failed: {result.stderr[:200]}")
        return False
    return True

def run_praat(wav_path: Path, pitch_csv: Path) -> bool:
    """Run Praat script to extract F0 into a CSV."""
    script_text = PRAAT_SCRIPT_TEMPLATE.format(
        input_path  = str(wav_path).replace("\\", "/"),
        output_path = str(pitch_csv).replace("\\", "/"),
        time_step   = TIME_STEP,
        f0_min      = F0_MIN,
        f0_max      = F0_MAX
    )
    script_path = TEMP_DIR / f"_script_{wav_path.stem}.praat"
    script_path.write_text(script_text, encoding="utf-8")

    result = subprocess.run(
        [PRAAT_EXE, "--run", str(script_path)],
        capture_output=True, text=True
    )
    script_path.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"  [ERROR] Praat failed: {result.stderr[:300]}")
        return False
    return True

def main():
    mp4_files = sorted(CLIPS_DIR.glob("GH*.mp4"))
    if not mp4_files:
        raise SystemExit(f"No GH*.mp4 files found in {CLIPS_DIR}")

    all_contour_rows = []
    all_peak_rows    = []

    for mp4 in mp4_files:
        file_id  = mp4.stem
        wav_path = TEMP_DIR / f"{file_id}.wav"
        tmp_csv  = TEMP_DIR / f"{file_id}_pitch.csv"

        print(f"Processing {file_id}...")

        # Step 1: extract WAV
        if not extract_wav(mp4, wav_path):
            print(f"  [SKIP] {file_id} - WAV extraction failed")
            continue

        # Step 2: run Praat on WAV
        if not run_praat(wav_path, tmp_csv):
            print(f"  [SKIP] {file_id} - Praat failed")
            wav_path.unlink(missing_ok=True)
            continue

        # Step 3: read Praat output
        with tmp_csv.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        # Clean up temp files
        wav_path.unlink(missing_ok=True)
        tmp_csv.unlink(missing_ok=True)

        if not rows:
            print(f"  [WARN] {file_id} - Praat produced no output")
            continue

        print(f"  {file_id}: {len(rows)} F0 frames extracted")

        # Contours: every valid frame
        times   = [int(r["time_ms"])    for r in rows]
        pitches = [float(r["pitch_hz"]) for r in rows]

        for t, p in zip(times, pitches):
            all_contour_rows.append({"file": file_id, "time_ms": t, "pitch_hz": p})

        # Peaks: local maxima
        for i in range(1, len(pitches) - 1):
            if pitches[i] > pitches[i-1] and pitches[i] > pitches[i+1]:
                all_peak_rows.append({"file": file_id, "time_ms": times[i], "pitch_hz": pitches[i]})

    # Write final CSVs
    with (OUT_DIR / "pitch_contours.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file", "time_ms", "pitch_hz"])
        w.writeheader()
        w.writerows(all_contour_rows)

    with (OUT_DIR / "pitch_peaks.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file", "time_ms", "pitch_hz"])
        w.writeheader()
        w.writerows(all_peak_rows)

    # Clean up temp folder if empty
    try:
        TEMP_DIR.rmdir()
    except OSError:
        pass

    print(f"\nDone. Contour frames: {len(all_contour_rows)}, Peaks: {len(all_peak_rows)}")

if __name__ == "__main__":
    main()