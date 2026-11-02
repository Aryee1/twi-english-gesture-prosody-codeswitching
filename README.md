# Gesture and Prosody at Twi–English Code Switching (Multimodal Pipeline)

This repository contains the code and derived outputs for a multimodal study of Twi–English code switching, focused on how **gesture strokes** align with **pitch peaks** around switch boundaries.

Dataset (ELAN annotations + derived features) is hosted on Zenodo: https://doi.org/10.5281/zenodo.23891055 (Version 1.1.0; v1.0.0 is https://doi.org/10.5281/zenodo.18731097)

## Corrected analysis (v1.1.0) — start here

The RQ2/RQ3 numbers from the first version were revised after an audit. **Do not use** the earlier overlap-based density (2.30×, 3.03×, d = 4.68) or the "51.6% within 50 ms of a pitch peak" figure; both were inflated by the method (long gesture intervals vs 1 s windows; one raw F0 peak every ~70 ms).

Current method and results (`scripts/15_final_stats.py` → `results/`):
- **RQ3 density:** each gesture counted once at its onset, speech time only, circular-shift permutation of windows (5,000 shuffles). Inside 0.308 vs outside 0.189 onsets/s = **1.63×** (p = .0002); paired t(10) = 4.89, Wilcoxon p = .002, dz = 1.47; 10 of 11 clips; both switch directions; ratio varies by speaker (1.21×–2.22×, four speakers).
- **RQ2 alignment:** nearest prominence-filtered F0 peak, permutation null drawn within speech. On the 643 in-speech onsets: 24.9% within 50 ms vs 23.1% expected (p = .15) — **chance level**.

Reproduce:
```bash
python scripts/15_final_stats.py results/
python scripts/16_make_figs.py
```
Scripts `12`–`14` are the audit steps that led to the revised method. Earlier density/alignment scripts (`07`, `08`) reflect the superseded method.

## What you will find here
- `scripts/`: the full analysis pipeline (ELAN extraction, speech activity detection, switch windows, pitch extraction, alignment, statistics)
- `annotations/`: ELAN `.eaf` files and templates for clips `GH001`–`GH011`
- `data_index/`: derived tables and figures produced by the pipeline
- `docs/figures/`: figures used for quick inspection and reporting

## Key outputs
- Gesture–pitch alignment summary: `data_index/alignment_analysis.csv`
- Per gesture type alignment table: `data_index/alignment_by_gesture_type.csv`
- Alignment figure: `docs/figures/alignment_histogram.png`
- Switch window density figure: `docs/figures/rq3_density_comparison.png`

## Quick start (no videos required)
If you only want to reproduce the **analysis outputs** from the provided derived tables:

1. Create an environment and install dependencies
   ```bash
   pip install -r requirements.txt
   ```

2. Recompute alignment and figures from the included CSVs
   ```bash
   python scripts/06_align_gesture_pitch.py
   python scripts/07_analyze_alignment.py
   python scripts/08_rq3_visualize_and_statistical.py
   ```

These steps use `data_index/gestures.csv` and `data_index/pitch_peaks.csv` that are already included in the repo.

## Full pipeline (requires videos)
Some scripts require local access to the MP4 clips and external tools:

- **FFmpeg** is required for speech activity detection and audio extraction.
- **Praat** is required for pitch extraction (see `scripts/05_extract_pitch.py` and set `PRAAT_EXE`).

Expected local layout (videos are not committed to GitHub):
- `data/clips/GH001.mp4` … `data/clips/GH011.mp4`

Then run, in order:
```bash
python scripts/01_extract_elan.py
python scripts/02_detect_speech_ffmpeg.py
python scripts/03_build_language_and_switches.py
python scripts/04_rq3_gesture_density.py
python scripts/05_extract_pitch.py
python scripts/06_align_gesture_pitch.py
python scripts/07_analyze_alignment.py
python scripts/08_rq3_visualize_and_statistical.py
```

## Citation
If you use the dataset, cite:
Aryee, M. A. (2026). *Twi–English code-switching multimodal dataset (ELAN annotations + derived features)* (Version 1.1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.23891055

The earlier LingBuzz preprint (https://lingbuzz.net/lingbuzz/009819) reports the superseded v1.0.0 analysis; cite the revised paper once available.

If you use this code, please cite the repository using the `CITATION.cff` file in the root.

## License
- Code: MIT (see `LICENSE`)
- Data: CC BY 4.0 via the Zenodo dataset record
