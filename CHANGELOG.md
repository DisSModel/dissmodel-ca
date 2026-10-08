# Changelog

## [0.1.0] — 2026-10-08

First citable release.

- Models compatible with dissmodel 0.5.0 or later (tested with 0.5.0, 0.6.0 and 0.6.6).
- `tests/test_models_smoke.py` runs every exported model for a few steps, headless,
  and checks that the grid is not corrupted; a GitHub Actions workflow runs it.
- `Excitable`, `Parity` and `Wolfram` raise a `ValueError` on a grid too small
  for their fixed seeds (Excitable, Parity: 50×50; Wolfram: `xdim` columns ×
  `final_time + 1` rows). Before, the seed assignment silently appended rows
  without geometry and the simulation ran on a corrupted grid.
- `streamlit` is no longer a required dependency: no module of the package uses
  it, only the Streamlit examples (`pip install "dissmodel-ca[examples]"`).
- `demo/`: self-contained Streamlit app (Dockerfile, pinned requirements,
  Hugging Face Space header) that can be deployed on its own.
- MIT license and `CITATION.cff`.
