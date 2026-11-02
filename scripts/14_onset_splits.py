"""Onset-based density by switch direction and by speaker, with circular-shift null."""
import csv, numpy as np
from pathlib import Path
from scipy import stats
D = Path(__file__).resolve().parents[1] / "data_index"
rd = lambda p: list(csv.DictReader(open(D / p, encoding="utf-8")))
G, S, WD = {}, {}, {}
for g in rd("gestures.csv"): G.setdefault(g["file"], []).append(int(g["start_ms"]))
for s in rd("speech_segments.csv"): S.setdefault(s["file"], []).append((int(s["start_ms"]), int(s["end_ms"])))
for w in rd("switch_windows_500ms.csv"): WD.setdefault((w["file"], w["direction"]), []).append((int(w["window_start_ms"]), int(w["window_end_ms"])))
files = sorted(S); ST = 10; rng = np.random.default_rng(11)
spk = lambda f: "Abronye" if int(f[2:]) <= 3 else "Frimpong" if int(f[2:]) <= 7 else "Ofosuah" if int(f[2:]) <= 9 else "Afrifa"
def mask(iv, n):
    m = np.zeros(n, bool)
    for s, e in iv:
        a, b = max(0, s // ST), min(n, -(-e // ST))
        if b > a: m[a:b] = True
    return m
def stat(f, dirs, shift):
    n = int(max(max(e for _, e in S[f]), max(G[f])) // ST) + 400
    sm = mask(S[f], n)
    iv = [w for d in dirs for w in WD.get((f, d), [])]
    wm = np.roll(mask(iv, n), shift)
    on = np.array([min(n - 1, s // ST) for s in G[f]]); ok = sm[on]
    return (ok & wm[on]).sum() / max((wm & sm).sum() * ST / 1000, 1e-9), (ok & ~wm[on]).sum() / max((sm & ~wm).sum() * ST / 1000, 1e-9), n
def run(dirs, fl, shift=False):
    out = []
    for f in fl:
        n = stat(f, dirs, 0)[2]
        out.append(stat(f, dirs, int(rng.integers(0, n)) if shift else 0)[:2])
    return np.array(out)
def report(label, dirs, fl, N=1000, test=True):
    r = run(dirs, fl); a, b = r[:, 0], r[:, 1]
    ratio = a.mean() / b.mean(); line = f"{label:15s} inside {a.mean():.3f} outside {b.mean():.3f} ratio {ratio:.2f}x  higher inside in {(a>b).sum()}/{len(fl)} clips"
    if test:
        nr = np.array([ (lambda x: x[:,0].mean()/x[:,1].mean())(run(dirs, fl, True)) for _ in range(N)])
        line += f"  | null {nr.mean():.2f}x, p = {(np.sum(nr>=ratio)+1)/(N+1):.4f}"
    print(line)
both = ["Twi_to_English", "English_to_Twi"]
print("--- by direction (onset rule) ---")
report("combined", both, files); report("Twi->English", [both[0]], files); report("English->Twi", [both[1]], files)
print("--- by speaker (onset rule) ---")
for s in ["Abronye", "Frimpong", "Ofosuah", "Afrifa"]:
    report(s, both, [f for f in files if spk(f) == s])
