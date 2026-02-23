"""
03_build_language_and_switches.py

Build:
- full_language_timeline.csv  (English + inferred Twi, speech only)
- switch_points.csv           (timestamp + direction)
- switch_windows_500ms.csv    (±500ms windows around switches)

Assumes these exist in data_index/:
  gestures.csv
  english_intervals.csv
  speech_segments.csv
"""

from pathlib import Path
import csv

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data_index"

WINDOW_MS = 500

def read_csv(path):
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

def subtract_intervals(base, subtract):
    """
    base and subtract are lists of (start,end) in ms
    returns base - subtract
    """
    result = []
    for b_start, b_end in base:
        segments = [(b_start, b_end)]
        for s_start, s_end in subtract:
            new_segments = []
            for seg_start, seg_end in segments:
                if s_end <= seg_start or s_start >= seg_end:
                    new_segments.append((seg_start, seg_end))
                else:
                    if s_start > seg_start:
                        new_segments.append((seg_start, s_start))
                    if s_end < seg_end:
                        new_segments.append((s_end, seg_end))
            segments = new_segments
        result.extend(segments)
    return result

def main():
    english = read_csv(DATA_DIR / "english_intervals.csv")
    speech  = read_csv(DATA_DIR / "speech_segments.csv")

    by_file_eng = {}
    by_file_speech = {}

    for r in english:
        by_file_eng.setdefault(r["file"], []).append((int(r["start_ms"]), int(r["end_ms"])))

    for r in speech:
        by_file_speech.setdefault(r["file"], []).append((int(r["start_ms"]), int(r["end_ms"])))

    full_lang_rows = []
    switch_rows = []
    window_rows = []

    for file_id in sorted(by_file_speech.keys()):

        speech_intervals = sorted(by_file_speech[file_id])
        eng_intervals = sorted(by_file_eng.get(file_id, []))

        # Infer Twi
        twi_intervals = subtract_intervals(speech_intervals, eng_intervals)

        combined = []
        for s,e in eng_intervals:
            combined.append(("English", s, e))
        for s,e in twi_intervals:
            combined.append(("Twi", s, e))

        combined.sort(key=lambda x: x[1])

        # Save full language timeline
        for label, s, e in combined:
            full_lang_rows.append({
                "file": file_id,
                "language": label,
                "start_ms": s,
                "end_ms": e,
                "dur_ms": e - s
            })

        # Compute switches
        for i in range(1, len(combined)):
            prev_lang, _, prev_end = combined[i-1]
            curr_lang, curr_start, _ = combined[i]

            if prev_lang != curr_lang:
                switch_time = curr_start
                direction = f"{prev_lang}_to_{curr_lang}"

                switch_rows.append({
                    "file": file_id,
                    "switch_time_ms": switch_time,
                    "direction": direction
                })

                window_rows.append({
                    "file": file_id,
                    "direction": direction,
                    "window_start_ms": max(0, switch_time - WINDOW_MS),
                    "window_end_ms": switch_time + WINDOW_MS
                })

    write_csv(DATA_DIR / "full_language_timeline.csv",
              full_lang_rows,
              ["file","language","start_ms","end_ms","dur_ms"])

    write_csv(DATA_DIR / "switch_points.csv",
              switch_rows,
              ["file","switch_time_ms","direction"])

    write_csv(DATA_DIR / "switch_windows_500ms.csv",
              window_rows,
              ["file","direction","window_start_ms","window_end_ms"])

    print("Wrote:")
    print("  full_language_timeline.csv")
    print("  switch_points.csv")
    print("  switch_windows_500ms.csv")

if __name__ == "__main__":
    main()