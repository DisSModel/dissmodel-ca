# Changelog

## [Unreleased]

Six models now follow the TerraME `ca` package (https://github.com/terrame/ca),
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
- `GameOfLife` (vector and raster): the Moore neighborhood wraps around the
  grid edges, as in TerraME's `Life` (`wrap = true`); `wrap=False` keeps the
  bounded grid. A glider now crosses the edge instead of dying on it.
- `FireModel` (raster): the fire spreads to the four Von Neumann neighbors,
  as in TerraME and in the vector version. The rule passed no neighborhood
  to `focal_sum_mask`, which counts all eight (Moore), so the fire also
  spread diagonally.
- `SolidDiffusion`: the step follows TerraME. Each vacancy draws one of all
  its neighbors (a vacancy may draw another vacancy and stay put) and moves
  at most once per step, reading the state at the start of the step. The
  port drew only among atoms and could move a vacancy several times in one
  step, so the atoms mixed faster than in TerraME (after 400 steps, 35.9
  atoms of one kind past the middle column against 26.5 in TerraME; now
  27).
- `tests/test_goldens.py` (marker `golden`): the models against TerraME 2.0.1
  runs from `terrame-goldens` v0.1.0. Deterministic models start from
  TerraME's state and must match it cell by cell; stochastic ones are
  compared with 50 TerraME runs by a Kolmogorov-Smirnov test and a test on
  the means. About a minute by default; `DISSMODEL_GOLDEN_FULL=1` compares
  every step and adds the slow ensembles. `tests/goldens/` holds the
  extract, its SHA-256 provenance and the script that makes it.
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
