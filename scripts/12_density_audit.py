"""
12_density_audit.py
Audit of the RQ3 density result:
 (a) speech-only density (windows clipped to speech, pauses excluded from
     both numerator and denominator)
 (b) circular-shift permutation baseline for window positions
 (c) paired t-test (df = n-1) alongside the independent one
 (d) speaker-level (n = 4) pooled check
 (e) diagnosis of combined vs per-direction ratios
"""
import csv
import numpy as np
from pathlib import Path
from scipy import stats

DATA = Path(__file__).resolve().parents[1] / "data_index"
STEP = 10  # ms grid
rng = np.random.default_rng(42)

def rd(p):
    with open(DATA / p, encoding="utf-8") as f:
        return list(csv.DictReader(f))

gest, wins, sp = rd("gestures.csv"), rd("switch_windows_500ms.csv"), rd("speech_segments.csv")
G, W, S, WD = {}, {}, {}, {}
for g in gest: G.setdefault(g["file"], []).append((int(g["start_ms"]), int(g["end_ms"])))
for w in wins:
    W.setdefault(w["file"], []).append((int(w["window_start_ms"]), int(w["window_end_ms"])))
    WD.setdefault((w["file"], w["direction"]), []).append((int(w["window_start_ms"]), int(w["window_end_ms"])))
for s in sp: S.setdefault(s["file"], []).append((int(s["start_ms"]), int(s["end_ms"])))

files = sorted(S)
speaker = {f: ("Abronye" if int(f[2:]) <= 3 else "Frimpong" if int(f[2:]) <= 7 else "Ofosuah" if int(f[2:]) <= 9 else "Afrifa") for f in files}

def mask(intervals, n):
    m = np.zeros(n, dtype=bool)
    for s, e in intervals:
        a, b = max(0, int(s // STEP)), min(n, int(np.ceil(e / STEP)))
        if b > a: m[a:b] = True
    return m

def clip_stats(f, shift=0, dirs=None):
    T = max(max(e for _, e in S[f]), max(e for _, e in G[f]), max(e for _, e in W[f])) + 1000
    n = int(T // STEP) + 2
    sm = mask(S[f], n)
    wl = W[f] if dirs is None else WD.get((f, dirs), [])
    wm = np.roll(mask(wl, n), shift)
    inside_m = wm & sm
    out_m = sm & ~wm
    cs_sp = np.concatenate([[0], np.cumsum(sm)])
    cs_in = np.concatenate([[0], np.cumsum(inside_m)])
    nin = nout = 0
    for gs, ge in G[f]:
        a, b = int(gs // STEP), min(n, int(np.ceil(ge / STEP)))
        if b <= a: continue
        if cs_sp[b] - cs_sp[a] == 0: continue  # stroke entirely outside speech
        if cs_in[b] - cs_in[a] > 0: nin += 1
        else: nout += 1
    tin, tout = inside_m.sum() * STEP / 1000, out_m.sum() * STEP / 1000
    return nin, nout, tin, tout, n

def per_clip(shift_fn=None, dirs=None):
    din, dout = [], []
    for f in files:
        T_bins = clip_stats(f, 0, dirs)[4]
        sh = 0 if shift_fn is None else int(shift_fn(T_bins))
        nin, nout, tin, tout, _ = clip_stats(f, sh, dirs)
        din.append(nin / tin if tin > 0 else 0)
        dout.append(nout / tout if tout > 0 else 0)
    return np.array(din), np.array(dout)

# (a) speech-only observed
din, dout = per_clip()
print("=== (a) Speech-only density (windows clipped to speech; pauses excluded) ===")
print(f"inside {din.mean():.3f}  outside {dout.mean():.3f}  ratio of means {din.mean()/dout.mean():.2f}x  mean per-clip ratio {np.mean(din/dout):.2f}x")
print("per-clip ratios:", np.round(din / dout, 2))

# (c) tests
t_ind = stats.ttest_ind(din, dout)
t_rel = stats.ttest_rel(din, dout)
w = stats.wilcoxon(din, dout)
print(f"independent t(20) = {t_ind.statistic:.2f}, p = {t_ind.pvalue:.2g}")
print(f"paired t(10)      = {t_rel.statistic:.2f}, p = {t_rel.pvalue:.2g}")
print(f"Wilcoxon W = {w.statistic}, p = {w.pvalue:.4g}")

# (b) circular-shift permutation baseline
N = 2000
null_ratio = np.zeros(N)
null_diff = np.zeros(N)
for i in range(N):
    a, b = per_clip(shift_fn=lambda T: rng.integers(0, T))
    null_ratio[i] = np.mean(a / np.where(b > 0, b, np.nan))
    null_diff[i] = np.nanmean(a - b)
obs_ratio = np.mean(din / dout)
obs_diff = np.mean(din - dout)
print("\n=== (b) Circular-shift permutation baseline (same windows, random position) ===")
print(f"null mean per-clip ratio {np.nanmean(null_ratio):.2f}x (SD {np.nanstd(null_ratio):.2f}); 95th pct {np.nanpercentile(null_ratio, 95):.2f}x; observed {obs_ratio:.2f}x")
print(f"p (ratio) = {(np.sum(null_ratio >= obs_ratio) + 1) / (N + 1):.4f}   p (diff) = {(np.sum(null_diff >= obs_diff) + 1) / (N + 1):.4f}")

# (d) speaker-level
print("\n=== (d) Speaker-level pooled (n = 4 speakers) ===")
for spk in ["Abronye", "Frimpong", "Ofosuah", "Afrifa"]:
    idx = [i for i, f in enumerate(files) if speaker[f] == spk]
    nin = sum(clip_stats(files[i])[0] for i in idx); nout = sum(clip_stats(files[i])[1] for i in idx)
    tin = sum(clip_stats(files[i])[2] for i in idx); tout = sum(clip_stats(files[i])[3] for i in idx)
    print(f"{spk:9s} inside {nin/tin:.3f}  outside {nout/tout:.3f}  ratio {(nin/tin)/(nout/tout):.2f}x")

# (e) diagnose combined vs directional
print("\n=== (e) Combined vs directional (speech-only) ===")
for label, d in [("combined", None), ("Twi_to_English", "Twi_to_English"), ("English_to_Twi", "English_to_Twi")]:
    a, b = per_clip(dirs=d)
    print(f"{label:15s} inside {a.mean():.3f}  outside {b.mean():.3f}  ratio {a.mean()/b.mean():.2f}x")
tot_sum, tot_union = 0, 0
for f in files:
    T = clip_stats(f)[4]
    ma = mask(WD.get((f, "Twi_to_English"), []), T); mb = mask(WD.get((f, "English_to_Twi"), []), T)
    tot_sum += (ma.sum() + mb.sum()); tot_union += (ma | mb).sum()
print(f"summed direction-window time / union time = {tot_sum / tot_union:.2f} (1.0 = no overlap)")
