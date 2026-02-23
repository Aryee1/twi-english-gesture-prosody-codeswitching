## Pipeline overview

This project follows an end to end multimodal pipeline:

1. Extract ELAN annotations (gesture strokes, English intervals)
2. Detect speech segments from audio (FFmpeg)
3. Build switch points and ±500 ms switch windows
4. Compute gesture density inside vs outside switch windows
5. Extract pitch contours and pitch peaks (Praat)
6. Align gesture stroke onsets to nearest pitch peaks
7. Summarise alignment and generate figures
8. Run paired statistics for density comparisons

A Mermaid diagram is included below for easy rendering on GitHub.

```mermaid
flowchart TD
  A[ELAN .eaf] --> B[01_extract_elan.py]
  V[MP4 clips] --> C[02_detect_speech_ffmpeg.py]
  B --> D[03_build_language_and_switches.py]
  C --> D
  D --> E[04_rq3_gesture_density.py]
  V --> F[05_extract_pitch.py]
  F --> G[06_align_gesture_pitch.py]
  E --> H[08_rq3_visualize_and_statistical.py]
  G --> I[07_analyze_alignment.py]
  I --> J[Figures + alignment tables]
  H --> K[Density figures + stats]
```
