# Changelog

## [Unreleased]

Four models now follow the TerraME `ca` package (https://github.com/terrame/ca),
where they used to differ. The results of these models change; a new minor
release (0.2.0) is suggested.

- `Parity`: the Von Neumann neighborhood wraps around the grid edges, as in
  TerraME (`wrap = true`); `setup(wrap=False)` keeps the bounded grid.
- `Excitable`: the seeds are at TerraME's (x=20, y=25) and (x=30, y=25),
  index `"25-20"` and `"25-30"`; they were at row 15. The smallest valid grid
  is now 31 columns × 26 rows.
- `Growth`: Von Neumann (Rook) neighborhood, as in TerraME; it was Queen.
- `FireModel` (vector and raster): new state `EMPTY = 3` (no vegetation, never
  burns) and new parameter `empty` (default 0.1). By default a single cell,
  drawn among all cells, starts burning, as in TerraME;
  `initial_fire_density` now defaults to 0.0 and, above zero, starts a random
  fraction of the cells burning instead (with `empty=0` and a density of
  0.05 the old setup is recovered, though not the same random draw).
- New `dissmodel_ca.models._neighborhood.grid_neighbors`: Von Neumann or Moore
  neighborhoods built from the `"row-col"` index, with optional wrap.
- `tests/test_terrame_rules.py`: Parity and Excitable are compared step by step
  with a NumPy transcription of the Lua rules; Growth and Fire are checked for
  neighborhood and initial state. The tests fail on the previous code.
- Fire notebook, Streamlit example and `docs/reference.md` updated (four
  states, fixed colour scale); Growth and Parity notes updated.

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
