"""
06_align_gesture_pitch.py
Align gestures with pitch peaks.

Outputs:
  data_index/gesture_pitch_alignment.csv
"""

from pathlib import Path
import csv
import bisect
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data_index"


def read_csv(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_pitch_index(pitch_peaks_rows):
    """
    Returns:
      dict[file] = (times_sorted: list[int], pitches_sorted: list[float])
    """
    tmp = defaultdict(list)
    for r in pitch_peaks_rows:
        file_id = r["file"]
        t = int(r["time_ms"])
        hz = float(r["pitch_hz"])
        tmp[file_id].append((t, hz))

    out = {}
    for file_id, pairs in tmp.items():
        pairs.sort(key=lambda x: x[0])
        times = [t for t, _ in pairs]
        pitches = [hz for _, hz in pairs]
        out[file_id] = (times, pitches)

    return out


def nearest_pitch_peak(gesture_time_ms: int, times: list[int], pitches: list[float]):
    """
    Find the closest pitch peak time to gesture_time_ms.
    Assumes times is sorted ascending.
    """
    if not times:
        return None, None

    i = bisect.bisect_left(times, gesture_time_ms)

    if i == 0:
        j = 0
    elif i >= len(times):
        j = len(times) - 1
    else:
        before = times[i - 1]
        after = times[i]
        j = i - 1 if (gesture_time_ms - before) <= (after - gesture_time_ms) else i

    return pitches[j], times[j]


def main():
    gestures = read_csv(DATA_DIR / "gestures.csv")
    pitch_peaks = read_csv(DATA_DIR / "pitch_peaks.csv")

    pitch_index = build_pitch_index(pitch_peaks)

    alignment_rows = []

    for g in gestures:
        file_id = g["file"]
        g_start_ms = int(g["start_ms"])

        if file_id not in pitch_index:
            continue

        times, pitches = pitch_index[file_id]
        pitch_hz, pitch_time_ms = nearest_pitch_peak(g_start_ms, times, pitches)
        if pitch_time_ms is None:
            continue

        alignment_rows.append({
            "file": file_id,
            "gesture_id": g["stroke_id"],
            "gesture_time_ms": g_start_ms,
            "gesture_type": g["gesture_type"],
            "pitch_time_ms": pitch_time_ms,
            "pitch_hz": pitch_hz,
            "time_diff_ms": g_start_ms - pitch_time_ms
        })

    output_file = DATA_DIR / "gesture_pitch_alignment.csv"
    if not alignment_rows:
        raise RuntimeError("No alignment rows were produced. Check that pitch_peaks.csv matches your gestures.csv files.")

    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=alignment_rows[0].keys())
        writer.writeheader()
        writer.writerows(alignment_rows)

    print("Wrote data_index/gesture_pitch_alignment.csv")


if __name__ == "__main__":
    main()