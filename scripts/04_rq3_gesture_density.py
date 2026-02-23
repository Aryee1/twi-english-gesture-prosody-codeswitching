"""
04_rq3_gesture_density.py

RQ3:
Compare gesture density inside ±500ms switch windows
vs outside those windows (speech only).

Outputs:
  rq3_gesture_density.csv
"""

from pathlib import Path
import csv

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data_index"

def read_csv(path):
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def overlaps(a_start, a_end, b_start, b_end):
    return not (a_end <= b_start or a_start >= b_end)

def main():
    gestures = read_csv(DATA_DIR / "gestures.csv")
    windows  = read_csv(DATA_DIR / "switch_windows_500ms.csv")
    speech   = read_csv(DATA_DIR / "speech_segments.csv")

    by_file_gest = {}
    by_file_win = {}
    by_file_speech = {}

    for g in gestures:
        by_file_gest.setdefault(g["file"], []).append(
            (int(g["start_ms"]), int(g["end_ms"]))
        )

    for w in windows:
        by_file_win.setdefault(w["file"], []).append(
            (int(w["window_start_ms"]), int(w["window_end_ms"]))
        )

    for s in speech:
        by_file_speech.setdefault(s["file"], []).append(
            (int(s["start_ms"]), int(s["end_ms"]))
        )

    rows = []

    for file_id in by_file_speech.keys():

        gestures_f = by_file_gest.get(file_id, [])
        windows_f  = by_file_win.get(file_id, [])
        speech_f   = by_file_speech[file_id]

        # total speech time
        total_speech_time = sum(e - s for s, e in speech_f)

        # total window time (not merging overlaps for simplicity; small error acceptable)
        total_window_time = sum(e - s for s, e in windows_f)

        # gestures inside windows
        inside = 0
        outside = 0

        for g_start, g_end in gestures_f:
            in_window = False
            for w_start, w_end in windows_f:
                if overlaps(g_start, g_end, w_start, w_end):
                    in_window = True
                    break
            if in_window:
                inside += 1
            else:
                outside += 1

        outside_time = total_speech_time - total_window_time

        density_inside = inside / (total_window_time / 1000) if total_window_time > 0 else 0
        density_outside = outside / (outside_time / 1000) if outside_time > 0 else 0

        rows.append({
            "file": file_id,
            "gestures_inside": inside,
            "gestures_outside": outside,
            "window_time_ms": total_window_time,
            "speech_time_ms": total_speech_time,
            "density_inside_per_sec": round(density_inside, 3),
            "density_outside_per_sec": round(density_outside, 3)
        })

    out = DATA_DIR / "rq3_gesture_density.csv"

    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    print("Wrote rq3_gesture_density.csv")

if __name__ == "__main__":
    main()