import json, csv, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
F = "results/"
B = "docs/figures/"
R = json.load(open(F + "results.json"))
BLUE, ORANGE, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK, "axes.spines.top": False, "axes.spines.right": False})

# ---- Figure 4: permutation null, all onsets vs speech-only onsets
n_all, n_sp = np.load(F + "null50.npy"), np.load(F + "null50_sp.npy")
o_all, o_sp = R["rq2_all"]["table"]["All"][3], R["rq2_speech_only"]["table"]["All"][3]
fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.6), sharey=True)
for a, null, o, title, n in [(ax[0], n_all, o_all, "All onsets (n = 837)", 837), (ax[1], n_sp, o_sp, "Onsets inside speech (n = 643)", 643)]:
    a.hist(null, bins=28, color=BLUE, alpha=0.55, edgecolor="white", linewidth=0.5, label="Permutation null (1,000 shuffles)")
    a.axvline(o, color=ORANGE, lw=2.2, label="Observed")
    a.axvline(null.mean(), color=MUTED, lw=1.1, ls="--", label="Null mean")
    a.set_title(title, fontsize=9.5, loc="left", color=INK); a.set_xlabel("% of onsets within 50 ms of a prosodic F0 peak")
    a.grid(axis="y", color=GRID, lw=0.6); a.set_axisbelow(True); a.set_xlim(17, 29)
ax[0].set_ylabel("Permutations"); h, l = ax[1].get_legend_handles_labels()
fig.legend(h, ["Permutation null (1,000 shuffles)", "Observed", "Null mean"], loc="lower center", ncol=3, frameon=False, fontsize=8)
plt.tight_layout(rect=(0, 0.07, 1, 1)); plt.savefig(B + "rq2_permutation_null.png", dpi=220); plt.close()

# ---- Figure 5: per-clip density + window-shift null for the ratio
rows = list(csv.DictReader(open(F + "per_clip.csv")))
clips = [r["clip"] for r in rows]; din = [float(r["dens_in"]) for r in rows]; dout = [float(r["dens_out"]) for r in rows]
nr = np.load(F + "null_ratio_combined.npy"); obs = R["rq3_combined"]["ratio_of_means"]
fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.9), gridspec_kw={"width_ratios": [1.5, 1]})
x = np.arange(len(clips)); w = 0.38
ax[0].bar(x - w/2 - 0.01, din, w, color=BLUE, label="Inside ±500 ms windows"); ax[0].bar(x + w/2 + 0.01, dout, w, color=ORANGE, label="Outside windows")
ax[0].set_xticks(x); ax[0].set_xticklabels([c.replace("GH0", "") for c in clips]); ax[0].set_xlabel("Clip (GH001–GH011)"); ax[0].set_ylabel("Gesture onsets per second of speech")
ax[0].grid(axis="y", color=GRID, lw=0.6); ax[0].set_axisbelow(True); ax[0].set_ylim(0, 0.56); ax[0].legend(frameon=False, fontsize=7.5, loc="upper left", ncol=2)
ax[0].set_title("Per-clip density (speech time only)", fontsize=9.5, loc="left")
ax[1].hist(nr, bins=40, color=BLUE, alpha=0.55, edgecolor="white", linewidth=0.4, label="Window-shift null (5,000)")
ax[1].axvline(obs, color=ORANGE, lw=2.2, label=f"Observed = {obs:.2f}×"); ax[1].axvline(nr.mean(), color=MUTED, lw=1.1, ls="--", label=f"Null mean = {nr.mean():.2f}×")
ax[1].set_xlabel("Inside / outside density ratio"); ax[1].set_ylabel("Shuffles"); ax[1].set_title("Chance baseline", fontsize=9.5, loc="left")
ax[1].grid(axis="y", color=GRID, lw=0.6); ax[1].set_axisbelow(True); ax[1].set_xlim(0.6, 1.8); ax[1].legend(frameon=False, fontsize=7.2, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=1)
plt.tight_layout(); plt.savefig(B + "rq3_onset_density_permutation.png", dpi=220); plt.close()
print("ok")
