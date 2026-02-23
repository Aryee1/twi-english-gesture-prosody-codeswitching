"""
08_rq3_visualize_and_statistical.py
Visualize and analyze gesture density inside vs outside switch windows.

Outputs:
  data_index/rq3_statistical_comparison.csv
  data_index/rq3_density_comparison.png
"""

import numpy as np
import csv
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data_index"

def read_csv(path):
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def visualize_density_comparison(inside_densities, outside_densities):
    plt.figure(figsize=(8, 6))

    # Plot histograms for inside vs outside densities
    plt.hist(inside_densities, bins=20, alpha=0.5, label="Inside Switch", color='blue')
    plt.hist(outside_densities, bins=20, alpha=0.5, label="Outside Switch", color='orange')

    plt.title('Gesture Density Comparison (Inside vs Outside Switch Windows)')
    plt.xlabel('Density (Gestures per second)')
    plt.ylabel('Frequency')
    plt.legend(loc='upper right')
    plt.grid(True)

    # Save the histogram plot
    plt.savefig(DATA_DIR / "rq3_density_comparison.png")
    plt.close()

def perform_statistical_test(inside_densities, outside_densities):
    # Conduct t-test to compare means of inside vs outside densities
    t_stat, p_value = stats.ttest_ind(inside_densities, outside_densities)
    return t_stat, p_value

def main():
    # Read gesture density data
    density_data = read_csv(DATA_DIR / "rq3_gesture_density.csv")

    inside_densities = []
    outside_densities = []

    for row in density_data:
        inside_densities.append(float(row["density_inside_per_sec"]))
        outside_densities.append(float(row["density_outside_per_sec"]))

    # Visualize the density comparison
    visualize_density_comparison(inside_densities, outside_densities)

    # Statistical test
    t_stat, p_value = perform_statistical_test(inside_densities, outside_densities)

    # Save statistical results
    with open(DATA_DIR / "rq3_statistical_comparison.csv", mode="w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["t_stat", "p_value"])
        writer.writerow([t_stat, p_value])

    print("Wrote rq3_statistical_comparison.csv and rq3_density_comparison.png")

if __name__ == "__main__":
    main()