# Gesture and Prosody at Twi–English Code Switching (Multimodal Pipeline)

This repository contains the code and derived outputs for a multimodal study of Twi–English code switching, focused on how **gesture strokes** align with **pitch peaks** around switch boundaries.

Dataset (ELAN annotations + derived features) is hosted on Zenodo: https://doi.org/10.5281/zenodo.18731097

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
Aryee, A. (2026). *Twi–English code-switching multimodal dataset (ELAN annotations + derived features)* (Version 1.0.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.18731097

If you use this code, please cite the repository using the `CITATION.cff` file in the root.

## License
- Code: MIT (see `LICENSE`)
- Data: CC BY 4.0 via the Zenodo dataset record
