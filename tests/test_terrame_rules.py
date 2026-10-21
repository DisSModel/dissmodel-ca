"""
Checks that the models follow the TerraME ``ca`` package
(https://github.com/terrame/ca) where the two used to differ:

- Parity: Von Neumann neighborhood with wrap (``wrap = true``);
- Excitable: seeds at (x=20, y=25) and (x=30, y=25), bounded grid;
- Growth: Von Neumann neighborhood (``strategy = "vonneumann"``);
- Fire: 10% empty cells and a single ignition.

The deterministic models are compared step by step with a NumPy
transcription of the Lua rule. The grid row is TerraME's ``y``.
"""
from __future__ import annotations

import numpy as np
import pytest

from dissmodel.core import Environment
from dissmodel.geo import parse_idx, raster_grid, vector_grid

from dissmodel_ca.models import (
    Excitable,
    FireModel,
    FireModelRaster,
    FireState,
    Growth,
    Parity,
)
from dissmodel_ca.models._neighborhood import grid_neighbors

STEPS = 14   # Environment(start_time=0, end_time=STEPS) runs STEPS + 1 steps


def _to_array(gdf, n_rows: int, n_cols: int) -> np.ndarray:
    out = np.zeros((n_rows, n_cols), dtype=int)
    for idx, value in gdf["state"].items():
        row, col = parse_idx(idx)
        out[row, col] = value
    return out


def _von_neumann_count(mask: np.ndarray, wrap: bool) -> np.ndarray:
    m = mask.astype(int)
    if wrap:
        return sum(np.roll(m, shift, axis) for shift in (1, -1) for axis in (0, 1))
    p = np.pad(m, 1)
    return p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]


def _parity_lua(state: np.ndarray, wrap: bool = True) -> np.ndarray:
    # Parity.lua: count == 1 or count == 3 -> "on", else "off"
    return np.isin(_von_neumann_count(state == 1, wrap), (1, 3)).astype(int)


def _excitable_lua(state: np.ndarray) -> np.ndarray:
    # Excitable.lua: 0 -> 1 if any neighbor > 0; 1..5 -> next, 5 -> 0
    excited = _von_neumann_count(state > 0, wrap=False) > 0
    return np.where(state == 0, excited.astype(int), (state + 1) % 6)


def _run(model_cls, n_cols: int, n_rows: int, steps: int = STEPS):
    env = Environment(start_time=0, end_time=steps)
    gdf = vector_grid(dimension=(n_cols, n_rows), resolution=1, attrs={"state": 0})
    model = model_cls(gdf=gdf, dim=max(n_cols, n_rows))
    model.initialize()
    start = _to_array(gdf, n_rows, n_cols)
    env.run()
    return start, _to_array(gdf, n_rows, n_cols)


# --------------------------------------------------------------------------
# grid_neighbors
# --------------------------------------------------------------------------

def _labels(n_rows: int, n_cols: int) -> list[str]:
    return [f"{r}-{c}" for r in range(n_rows) for c in range(n_cols)]


def test_grid_neighbors_bounded_and_wrapped():
    labels = _labels(4, 5)
    bounded = grid_neighbors(labels, "vonneumann")
    wrapped = grid_neighbors(labels, "vonneumann", wrap=True)
    assert sorted(bounded["0-0"]) == ["0-1", "1-0"]
    assert sorted(wrapped["0-0"]) == ["0-1", "0-4", "1-0", "3-0"]
    assert all(len(v) == 4 for v in wrapped.values())
    assert all(len(v) == 8 for v in grid_neighbors(labels, "moore", wrap=True).values())


def test_grid_neighbors_narrow_grid_has_no_duplicates_or_self():
    wrapped = grid_neighbors(_labels(2, 2), "moore", wrap=True)
    for cell, neighbors in wrapped.items():
        assert cell not in neighbors
        assert len(neighbors) == len(set(neighbors)) == 3


def test_grid_neighbors_rejects_unknown_strategy():
    with pytest.raises(ValueError, match="strategy"):
        grid_neighbors(_labels(3, 3), "hexagonal")


# --------------------------------------------------------------------------
# Deterministic models against the Lua rule
# --------------------------------------------------------------------------

def test_parity_matches_lua_rule_with_wrap():
    # 42 x 27 is the smallest grid that holds both seeds; the seed at
    # x=40 reaches the right edge at once, so wrapping matters early.
    n_cols, n_rows = 42, 27
    start, end = _run(Parity, n_cols, n_rows)
    assert start[25, 10] == start[25, 40] == 1 and start.sum() == 2

    expected = start
    for _ in range(STEPS + 1):
        expected = _parity_lua(expected, wrap=True)
    np.testing.assert_array_equal(end, expected)

    bounded = start
    for _ in range(STEPS + 1):
        bounded = _parity_lua(bounded, wrap=False)
    assert not np.array_equal(end, bounded), "the test must tell wrap from no wrap"


def test_excitable_seeds_and_lua_rule():
    n_cols, n_rows = 32, 27
    start, end = _run(Excitable, n_cols, n_rows)
    assert start[25, 20] == start[25, 30] == 1 and start.sum() == 2

    expected = start
    for _ in range(STEPS + 1):
        expected = _excitable_lua(expected)
    np.testing.assert_array_equal(end, expected)


# --------------------------------------------------------------------------
# Stochastic models: neighborhood and initial state
# --------------------------------------------------------------------------

def test_growth_uses_von_neumann_neighborhood():
    Environment(start_time=0, end_time=1)
    gdf = vector_grid(dimension=(5, 5), resolution=1, attrs={"state": 0})
    model = Growth(gdf=gdf, dim=5)
    assert sorted(model.neighs_id("2-2")) == ["1-2", "2-1", "2-3", "3-2"]
    assert len(model.neighs_id("0-0")) == 2


def test_growth_only_spreads_to_von_neumann_neighbors():
    env = Environment(start_time=0, end_time=0)
    gdf = vector_grid(dimension=(5, 5), resolution=1, attrs={"state": 0})
    model = Growth(gdf=gdf, dim=5)
    model.probability = 1.0
    model.initialize()
    env.run()
    alive = sorted(gdf.index[gdf["state"] == 1])
    assert alive == ["1-2", "2-1", "2-2", "2-3", "3-2"]


def test_fire_default_is_terrame_setup():
    Environment(start_time=0, end_time=1)
    gdf = vector_grid(dimension=(60, 60), resolution=1, attrs={"state": 0})
    model = FireModel(gdf=gdf)
    model.initialize()
    counts = gdf["state"].value_counts()
    assert counts.get(FireState.BURNING, 0) == 1
    assert 0.07 < counts.get(FireState.EMPTY, 0) / len(gdf) < 0.13
    assert set(counts.index) <= {FireState.FOREST, FireState.BURNING, FireState.EMPTY}


def test_fire_empty_cells_never_burn():
    env = Environment(start_time=0, end_time=40)
    gdf = vector_grid(dimension=(20, 20), resolution=1, attrs={"state": 0})
    model = FireModel(gdf=gdf)
    model.setup(empty=0.3, initial_fire_density=0.2, seed=1)
    model.initialize()
    empty_before = set(gdf.index[gdf["state"] == FireState.EMPTY])
    env.run()
    assert set(gdf.index[gdf["state"] == FireState.EMPTY]) == empty_before


def test_fire_density_still_seeds_many_fires():
    Environment(start_time=0, end_time=1)
    gdf = vector_grid(dimension=(30, 30), resolution=1, attrs={"state": 0})
    model = FireModel(gdf=gdf)
    model.setup(empty=0.0, initial_fire_density=0.05)
    model.initialize()
    burning = (gdf["state"] == FireState.BURNING).sum()
    assert 20 < burning < 70
    assert (gdf["state"] == FireState.EMPTY).sum() == 0


@pytest.mark.parametrize("name, value", [("empty", 1.5), ("initial_fire_density", -0.1)])
def test_fire_rejects_probabilities_outside_unit_interval(name, value):
    Environment(start_time=0, end_time=1)
    gdf = vector_grid(dimension=(5, 5), resolution=1, attrs={"state": 0})
    model = FireModel(gdf=gdf)
    setattr(model, name, value)
    with pytest.raises(ValueError, match=name):
        model.initialize()


def test_fire_raster_default_is_terrame_setup():
    backend = raster_grid(rows=60, cols=60, attrs={"state": 0})
    Environment(start_time=0, end_time=1)
    model = FireModelRaster(backend=backend)
    model.initialize()
    state = backend.get("state")
    assert (state == FireState.BURNING).sum() == 1
    assert 0.07 < (state == FireState.EMPTY).mean() < 0.13
