"""
15_final_stats.py
Final corrected analyses for the Twi-English gesture-prosody paper.

RQ1  gesture type distribution
RQ2  gesture-onset proximity to prominence-filtered F0 peaks vs a permutation null
RQ3  gesture-onset density inside vs outside +/-500ms code-switch windows
     - onset-based (a stroke counts once, at its onset)
     - speech time only (pauses excluded from numerator and denominator)
     - chance baseline: circular shift of the window positions within each clip
     - paired tests (df = n_clips - 1), direction split, speaker split

Writes results.json and per-clip CSVs to the output directory given as argv[1].
"""
import csv, json, sys
from pathlib import Path
import numpy as np
from scipy import stats
from scipy.signal import find_peaks

DATA = Path(__file__).resolve().parents[1] / "data_index"
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
STEP = 10  # ms grid for masks
rd = lambda p: list(csv.DictReader(open(DATA / p, encoding="utf-8")))

gest, contour, speech, wins = rd("gestures.csv"), rd("pitch_contours.csv"), rd("speech_segments.csv"), rd("switch_windows_500ms.csv")
FILES = sorted({g["file"] for g in gest})
G, S, W, WD, C = {}, {}, {}, {}, {}
for g in gest: G.setdefault(g["file"], []).append((int(g["start_ms"]), int(g["end_ms"]), g["gesture_type"]))
for s in speech: S.setdefault(s["file"], []).append((int(s["start_ms"]), int(s["end_ms"])))
for w in wins:
    iv = (int(w["window_start_ms"]), int(w["window_end_ms"]))
    W.setdefault(w["file"], []).append(iv); WD.setdefault((w["file"], w["direction"]), []).append(iv)
for c in contour: C.setdefault(c["file"], []).append((float(c["time_ms"]), float(c["pitch_hz"])))
SPEAKER = lambda f: "Abronye DC" if int(f[2:]) <= 3 else "Frimpong" if int(f[2:]) <= 7 else "Ofosuah" if int(f[2:]) <= 9 else "Afrifa"
R = {}

# ---------------- RQ1 ----------------
types = [g[2] for f in FILES for g in G[f]]
R["rq1"] = {t: [types.count(t), 100 * types.count(t) / len(types)] for t in ["beat", "iconic", "deictic"]}
R["n_strokes"] = len(types)
dur = np.array([g[1] - g[0] for f in FILES for g in G[f]])
R["stroke_duration_ms"] = {"mean": float(dur.mean()), "median": float(np.median(dur)), "p90": float(np.percentile(dur, 90))}

def mask(iv, n):
    m = np.zeros(n, bool)
    for s, e in iv:
        a, b = max(0, int(s // STEP)), min(n, -(-int(e) // STEP))
        if b > a: m[a:b] = True
    return m
NB = {f: int(max(max(e for _, e in S[f]), max(g[0] for g in G[f]), max(e for _, e in W[f])) // STEP) + 100 for f in FILES}
SM = {f: mask(S[f], NB[f]) for f in FILES}
ON = {f: np.array([min(NB[f] - 1, int(g[0] // STEP)) for g in G[f]]) for f in FILES}
WU = {f: mask(W[f], NB[f]) for f in FILES}
WDm = {(f, d): mask(WD.get((f, d), []), NB[f]) for f in FILES for d in ["Twi_to_English", "English_to_Twi"]}

# ---------------- RQ2 ----------------
peaks = {}
for f in FILES:
    pts = sorted(C[f]); hz = np.array([p[1] for p in pts]); t = np.array([p[0] for p in pts])
    idx, _ = find_peaks(hz, distance=15, prominence=10)  # 150 ms, 10 Hz, over the voiced-frame sequence
    peaks[f] = np.sort(t[idx])
R["n_peaks_prominence"] = int(sum(len(v) for v in peaks.values()))

def nearest(times, pk):
    i = np.clip(np.searchsorted(pk, times), 1, len(pk) - 1)
    return np.minimum(np.abs(times - pk[i - 1]), np.abs(times - pk[i]))

def in_speech(f, t):
    return any(s <= t <= e for s, e in S[f])

obs = {f: np.array([g[0] for g in G[f]], float) for f in FILES}
types_f = {f: [g[2] for g in G[f]] for f in FILES}
insp = {f: SM[f][ON[f]] for f in FILES}
R["onsets_in_speech_pct"] = float(100 * np.mean(np.concatenate([insp[f] for f in FILES])))
R["n_onsets_in_speech"] = int(sum(insp[f].sum() for f in FILES))
R["speech_seconds"] = float(sum(e - s_ for f in FILES for s_, e in S[f]) / 1000)

def summarise(mask_fn):
    d_all, d_type = [], []
    for f in FILES:
        m = mask_fn(f)
        d = nearest(obs[f][m], peaks[f]); d_all.append(d); d_type += [t for t, k in zip(types_f[f], m) if k]
    d_all = np.concatenate(d_all); d_type = np.array(d_type)
    out = {"All": [len(d_all), d_all.mean(), np.median(d_all), 100 * np.mean(d_all <= 50), 100 * np.mean(d_all <= 100)]}
    for t in ["beat", "iconic", "deictic"]:
        x = d_all[d_type == t]; out[t] = [len(x), x.mean(), np.median(x), 100 * np.mean(x <= 50), 100 * np.mean(x <= 100)]
    return out

rng = np.random.default_rng(42)
def sample_onsets(f, n):
    st = np.array([s for s, e in S[f]], float); en = np.array([e for s, e in S[f]], float); du = en - st
    k = rng.choice(len(st), size=n, p=du / du.sum()); return st[k] + rng.random(n) * du[k]

NP = 1000
null50, null100, null50_sp, null100_sp = np.zeros(NP), np.zeros(NP), np.zeros(NP), np.zeros(NP)
for i in range(NP):
    d = np.concatenate([nearest(sample_onsets(f, len(obs[f])), peaks[f]) for f in FILES])
    null50[i], null100[i] = 100 * np.mean(d <= 50), 100 * np.mean(d <= 100)
# Version B: observed onsets restricted to those that fall inside speech; null has the same count per clip
all_obs = summarise(lambda f: np.ones(len(obs[f]), bool)); sp_obs = summarise(lambda f: insp[f])
for i in range(NP):
    d = np.concatenate([nearest(sample_onsets(f, int(insp[f].sum())), peaks[f]) for f in FILES])
    null50_sp[i], null100_sp[i] = 100 * np.mean(d <= 50), 100 * np.mean(d <= 100)
def pv(null, o): return {"null_mean": float(null.mean()), "null_sd": float(null.std()), "p_upper": float((np.sum(null >= o) + 1) / (NP + 1)), "p_lower": float((np.sum(null <= o) + 1) / (NP + 1))}
R["rq2_all"] = {"table": {k: [float(x) for x in v] for k, v in all_obs.items()}, "w50": pv(null50, all_obs["All"][3]), "w100": pv(null100, all_obs["All"][4])}
R["rq2_speech_only"] = {"table": {k: [float(x) for x in v] for k, v in sp_obs.items()}, "w50": pv(null50_sp, sp_obs["All"][3]), "w100": pv(null100_sp, sp_obs["All"][4])}

RAWP = {}
for r_ in rd("pitch_peaks.csv"): RAWP.setdefault(r_["file"], []).append(float(r_["time_ms"]))
RAWP = {f: np.sort(np.array(v)) for f, v in RAWP.items()}
R["n_raw_peaks"] = int(sum(len(v) for v in RAWP.values()))
R["raw_peaks_per_s"] = R["n_raw_peaks"] / R["speech_seconds"]; R["prom_peaks_per_s"] = R["n_peaks_prominence"] / R["speech_seconds"]
R["raw_median_gap_ms"] = float(np.median(np.concatenate([np.diff(v) for v in RAWP.values()])))
d_raw = np.concatenate([nearest(obs[f][insp[f]], RAWP[f]) for f in FILES])
ro50, ro100 = 100 * np.mean(d_raw <= 50), 100 * np.mean(d_raw <= 100)
n50r, n100r = np.zeros(NP), np.zeros(NP)
for i in range(NP):
    d = np.concatenate([nearest(sample_onsets(f, int(insp[f].sum())), RAWP[f]) for f in FILES])
    n50r[i], n100r[i] = 100 * np.mean(d <= 50), 100 * np.mean(d <= 100)
R["rq2_raw_peaks_speech_only"] = {"obs50": float(ro50), "obs100": float(ro100), "w50": pv(n50r, ro50), "w100": pv(n100r, ro100)}
np.save(OUT / "null50.npy", null50); np.save(OUT / "null50_sp.npy", null50_sp)

# ---------------- RQ3 ----------------

def counts(f, inside_mask, union_mask):
    ok = SM[f][ON[f]]
    nin = int((ok & inside_mask[ON[f]]).sum()); nout = int((ok & ~union_mask[ON[f]]).sum())
    tin = float((inside_mask & SM[f]).sum() * STEP / 1000); tout = float((SM[f] & ~union_mask).sum() * STEP / 1000)
    return nin, nout, tin, tout

def clip_table(inside_fn, union_fn, files, shifts=None):
    rows = []
    for f in files:
        sh = 0 if shifts is None else shifts[f]
        rows.append((f,) + counts(f, np.roll(inside_fn(f), sh), np.roll(union_fn(f), sh)))
    return rows

def dens(rows):
    din = np.array([r[1] / r[3] if r[3] > 0 else np.nan for r in rows]); dout = np.array([r[2] / r[4] if r[4] > 0 else np.nan for r in rows])
    return din, dout

def permute(inside_fn, union_fn, files, N=5000, seed=3):
    r = np.random.default_rng(seed); out = np.zeros(N); outd = np.zeros(N)
    for k in range(N):
        sh = {f: int(r.integers(0, NB[f])) for f in files}
        a, b = dens(clip_table(inside_fn, union_fn, files, sh)); out[k] = np.nanmean(a) / np.nanmean(b); outd[k] = np.nanmean(a - b)
    return out, outd

def analyse(label, inside_fn, union_fn, files, N=5000, tests=True):
    rows = clip_table(inside_fn, union_fn, files); a, b = dens(rows)
    ratio = a.mean() / b.mean(); res = {"n_clips": len(files), "inside": float(a.mean()), "outside": float(b.mean()), "ratio_of_means": float(ratio),
        "mean_clip_ratio": float(np.mean(a / b)), "clip_ratio_min": float(np.min(a / b)), "clip_ratio_max": float(np.max(a / b)), "clips_higher_inside": int((a > b).sum())}
    nr, nd = permute(inside_fn, union_fn, files, N)
    res.update({"null_ratio_mean": float(nr.mean()), "null_ratio_p95": float(np.percentile(nr, 95)), "p_perm_ratio": float((np.sum(nr >= ratio) + 1) / (N + 1)), "p_perm_diff": float((np.sum(nd >= (a - b).mean()) + 1) / (N + 1))})
    if tests and len(files) > 3:
        tr = stats.ttest_rel(a, b); w = stats.wilcoxon(a, b); dz = float((a - b).mean() / (a - b).std(ddof=1))
        res.update({"t": float(tr.statistic), "df": len(files) - 1, "p_t": float(tr.pvalue), "W": float(w.statistic), "p_w": float(w.pvalue), "cohens_dz": dz})
    return res, rows, nr

comb, rows, nr_comb = analyse("combined", lambda f: WU[f], lambda f: WU[f], FILES)
R["rq3_combined"] = comb
np.save(OUT / "null_ratio_combined.npy", nr_comb)
with open(OUT / "per_clip.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["clip", "inside_n", "outside_n", "inside_s", "outside_s", "dens_in", "dens_out", "ratio"])
    for r in rows: w.writerow([r[0], r[1], r[2], round(r[3], 2), round(r[4], 2), r[1] / r[3], r[2] / r[4], (r[1] / r[3]) / (r[2] / r[4])])
R["onsets_excluded_outside_speech"] = int(sum((~SM[f][ON[f]]).sum() for f in FILES))
R["window_time_union_over_sum_dirs"] = None
R["rq3_direction"] = {}
for d in ["Twi_to_English", "English_to_Twi"]:
    res, _, _ = analyse(d, lambda f, d=d: WDm[(f, d)], lambda f: WU[f], FILES, N=3000, tests=True)
    R["rq3_direction"][d] = res
R["rq3_speaker"] = {}
for spk in ["Abronye DC", "Frimpong", "Ofosuah", "Afrifa"]:
    fl = [f for f in FILES if SPEAKER(f) == spk]
    rows_s = clip_table(lambda f: WU[f], lambda f: WU[f], fl)
    nin, nout = sum(r[1] for r in rows_s), sum(r[2] for r in rows_s); tin, tout = sum(r[3] for r in rows_s), sum(r[4] for r in rows_s)
    r_ = np.random.default_rng(5); nul = np.zeros(3000)
    for k in range(3000):
        sh = {f: int(r_.integers(0, NB[f])) for f in fl}; rr = clip_table(lambda f: WU[f], lambda f: WU[f], fl, sh)
        nul[k] = (sum(x[1] for x in rr) / sum(x[3] for x in rr)) / (sum(x[2] for x in rr) / sum(x[4] for x in rr))
    ratio = (nin / tin) / (nout / tout)
    R["rq3_speaker"][spk] = {"clips": len(fl), "inside": nin / tin, "outside": nout / tout, "ratio": ratio, "null_mean": float(nul.mean()), "p": float((np.sum(nul >= ratio) + 1) / 3001)}

json.dump(R, open(OUT / "results.json", "w"), indent=1, default=float)
print(json.dumps(R, indent=1, default=float))
