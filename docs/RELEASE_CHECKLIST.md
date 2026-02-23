## Release checklist (suggested)

- [ ] Confirm dataset DOI in README: https://doi.org/10.5281/zenodo.18731097
- [ ] Replace `repository-code` in CITATION.cff with the GitHub URL
- [ ] Verify `data/` is ignored and no videos are tracked
- [ ] Run:
      - python scripts/06_align_gesture_pitch.py
      - python scripts/07_analyze_alignment.py
      - python scripts/08_rq3_visualize_and_statistical.py
- [ ] Push to GitHub and create a tag: v1.0.0
- [ ] Optional: connect GitHub releases to Zenodo for a software DOI
