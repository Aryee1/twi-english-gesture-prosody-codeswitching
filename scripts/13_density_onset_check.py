"""Onset-based density with circular-shift null; also stroke-duration stats."""
import csv, numpy as np
from pathlib import Path
from scipy import stats
D = Path(__file__).resolve().parents[1] / "data_index"
rd = lambda p: list(csv.DictReader(open(D / p, encoding="utf-8")))
G, W, S = {}, {}, {}
for g in rd("gestures.csv"): G.setdefault(g["file"], []).append((int(g["start_ms"]), int(g["end_ms"])))
for w in rd("switch_windows_500ms.csv"): W.setdefault(w["file"], []).append((int(w["window_start_ms"]), int(w["window_end_ms"])))
for s in rd("speech_segments.csv"): S.setdefault(s["file"], []).append((int(s["start_ms"]), int(s["end_ms"])))
files = sorted(S); ST = 10; rng = np.random.default_rng(7)
dur = np.array([e - s for f in files for s, e in G[f]])
print(f"stroke duration: mean {dur.mean():.0f} ms, median {np.median(dur):.0f}, 90th pct {np.percentile(dur,90):.0f}; window width 1000 ms")
def mask(iv, n):
    m = np.zeros(n, bool)
    for s, e in iv:
        a, b = max(0, s // ST), min(n, -(-e // ST))
        if b > a: m[a:b] = True
    return m
def clip(f, shift):
    n = int(max(max(e for _, e in S[f]), max(e for _, e in G[f]), max(e for _, e in W[f])) // ST) + 102
    sm = mask(S[f], n); wm = np.roll(mask(W[f], n), shift)
    on = np.array([min(n - 1, s // ST) for s, _ in G[f]])
    in_sp = sm[on]
    nin = int((in_sp & wm[on]).sum()); nout = int((in_sp & ~wm[on]).sum())
    return nin / max((wm & sm).sum() * ST / 1000, 1e-9), nout / max((sm & ~wm).sum() * ST / 1000, 1e-9), n
def run(shift=False):
    a, b = [], []
    for f in files:
        n = clip(f, 0)[2]
        i, o, _ = clip(f, int(rng.integers(0, n)) if shift else 0)
        a.append(i); b.append(o)
    return np.array(a), np.array(b)
a, b = run()
print(f"onset-based observed: inside {a.mean():.3f} outside {b.mean():.3f} mean per-clip ratio {np.mean(a/b):.2f}x")
print(f"paired t(10) = {stats.ttest_rel(a,b).statistic:.2f}, p = {stats.ttest_rel(a,b).pvalue:.3g}; Wilcoxon p = {stats.wilcoxon(a,b).pvalue:.4g}; clips higher inside: {(a>b).sum()}/11")
N = 2000; nr = np.zeros(N); nd = np.zeros(N)
for k in range(N):
    x, y = run(True); nr[k] = np.mean(x / np.where(y > 0, y, np.nan)); nd[k] = np.nanmean(x - y)
obs_r, obs_d = np.mean(a / b), np.mean(a - b)
print(f"null ratio mean {np.nanmean(nr):.2f}x (95th pct {np.nanpercentile(nr,95):.2f}x); p(ratio) = {(np.sum(nr>=obs_r)+1)/(N+1):.4f}; p(diff) = {(np.sum(nd>=obs_d)+1)/(N+1):.4f}")
