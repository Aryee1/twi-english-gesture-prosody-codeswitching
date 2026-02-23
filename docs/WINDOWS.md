## Running on Windows (VS Code)

1. Create a virtual environment
   - In VS Code terminal:
     - `python -m venv .venv`
     - `.venv\Scripts\activate`

2. Install requirements
   - `pip install -r requirements.txt`

3. Run the analysis from included derived tables
   - `python scripts\06_align_gesture_pitch.py`
   - `python scripts\07_analyze_alignment.py`
   - `python scripts\08_rq3_visualize_and_statistical.py`

For the full pipeline you also need FFmpeg on PATH and Praat installed (set `PRAAT_EXE` in `scripts/05_extract_pitch.py`).
