"""
07_analyze_alignment.py
Summarise gesture-pitch alignment and generate the alignment figure.

Inputs:
  data_index/gesture_pitch_alignment.csv

Outputs:
  data_index/alignment_analysis.csv
  data_index/alignment_by_gesture_type.csv
  data_index/alignment_histogram.png
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data_index"

INFILE = DATA_DIR / "gesture_pitch_alignment.csv"
OUT_ANALYSIS = DATA_DIR / "alignment_analysis.csv"
OUT_BY_TYPE = DATA_DIR / "alignment_by_gesture_type.csv"
OUT_FIG = DATA_DIR / "alignment_histogram.png"


def main():
    if not INFILE.exists():
        raise FileNotFoundError(f"Missing input: {INFILE}")

    df = pd.read_csv(INFILE)

    if "time_diff_ms" not in df.columns:
        raise ValueError("gesture_pitch_alignment.csv must contain 'time_diff_ms'")

    df["time_diff_ms"] = pd.to_numeric(df["time_diff_ms"], errors="coerce")
    df = df.dropna(subset=["time_diff_ms"]).copy()
    df["time_diff_ms"] = df["time_diff_ms"].astype(int)
    df["abs_diff_ms"] = df["time_diff_ms"].abs()

    n = int(len(df))
    mean_signed = float(df["time_diff_ms"].mean())
    median_signed = float(df["time_diff_ms"].median())
    std_signed = float(df["time_diff_ms"].std(ddof=1)) if n > 1 else 0.0
    min_signed = int(df["time_diff_ms"].min())
    max_signed = int(df["time_diff_ms"].max())

    mean_abs = float(df["abs_diff_ms"].mean())
    median_abs = float(df["abs_diff_ms"].median())

    p50 = float((df["abs_diff_ms"] <= 50).mean() * 100)
    p100 = float((df["abs_diff_ms"] <= 100).mean() * 100)

    # --- Write alignment_analysis.csv (single-row) ---
    analysis_row = pd.DataFrame([{
        "N": n,
        "Mean Difference (ms)": mean_signed,
        "Median Difference (ms)": median_signed,
        "Std Difference (ms)": std_signed,
        "Min Difference (ms)": min_signed,
        "Max Difference (ms)": max_signed,
        "Mean |Δt| (ms)": mean_abs,
        "Median |Δt| (ms)": median_abs,
        "Within 50 ms (%)": p50,
        "Within 100 ms (%)": p100,
    }])
    analysis_row.to_csv(OUT_ANALYSIS, index=False)

    # --- Write alignment_by_gesture_type.csv ---
    if "gesture_type" in df.columns:
        by_type = (
            df.groupby("gesture_type", dropna=False)
            .agg(
                N=("time_diff_ms", "size"),
                mean_abs=("abs_diff_ms", "mean"),
                median_abs=("abs_diff_ms", "median"),
                within_50=("abs_diff_ms", lambda x: (x <= 50).mean() * 100),
                within_100=("abs_diff_ms", lambda x: (x <= 100).mean() * 100),
            )
            .reset_index()
            .rename(columns={"gesture_type": "Gesture Type"})
        )

        # Formatting to match paper-friendly table style
        by_type["Mean |Δt| (ms)"] = by_type["mean_abs"].round(1)
        by_type["Median |Δt| (ms)"] = by_type["median_abs"].round(1)
        by_type["Within 50 ms (%)"] = by_type["within_50"].round(1)
        by_type["Within 100 ms (%)"] = by_type["within_100"].round(1)

        out_cols = [
            "Gesture Type",
            "N",
            "Mean |Δt| (ms)",
            "Median |Δt| (ms)",
            "Within 50 ms (%)",
            "Within 100 ms (%)",
        ]
        by_type[out_cols].to_csv(OUT_BY_TYPE, index=False)

    # --- Figure: histogram (signed) + cumulative curve (absolute) ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: signed histogram
    axes[0].hist(df["time_diff_ms"], bins=40)
    axes[0].axvline(0, linestyle="--", linewidth=1, label="Zero lag")
    axes[0].axvline(mean_signed, linewidth=1.5, label=f"Mean = {mean_signed:.1f} ms")
    axes[0].set_title(f"Distribution of Time Differences\n(N = {n} gesture strokes)")
    axes[0].set_xlabel("Time Difference (ms)\n[Gesture onset - Pitch peak]")
    axes[0].set_ylabel("Frequency")
    axes[0].legend()

    # Right: cumulative within threshold for abs diffs
    abs_vals = np.sort(df["abs_diff_ms"].to_numpy())
    thresholds = np.arange(0, max(abs_vals.max(), 1) + 1)
    # percent within threshold t is count(abs_vals <= t) / n
    counts = np.searchsorted(abs_vals, thresholds, side="right")
    cum_pct = counts / n * 100.0

    axes[1].plot(thresholds, cum_pct)
    axes[1].set_title("Cumulative Alignment within Threshold")
    axes[1].set_xlabel("Absolute Time Difference Threshold (ms)")
    axes[1].set_ylabel("Cumulative % of Gesture Strokes")
    axes[1].set_ylim(0, 101)

    # Mark 50 and 100 ms
    for t in (50, 100):
        if t <= thresholds[-1]:
            pct = cum_pct[t]
            axes[1].axvline(t, linestyle="--", linewidth=1)
            axes[1].axhline(pct, linestyle="--", linewidth=1)
            axes[1].text(t + 2, min(pct + 2, 99.5), f"{pct:.1f}%\nwithin {t}ms")

    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=200)
    plt.close(fig)

    print("Wrote:")
    print(f"  {OUT_ANALYSIS}")
    print(f"  {OUT_BY_TYPE}")
    print(f"  {OUT_FIG}")


if __name__ == "__main__":
    main()