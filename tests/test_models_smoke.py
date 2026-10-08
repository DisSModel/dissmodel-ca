"""
Smoke test: every cellular automaton exported by dissmodel_ca.models is
instantiated on a small grid and run for a few steps, headless.

It checks that the models work with the installed dissmodel and that the
state stays numeric with the right number of cells; it does not check the
dynamics of each model.
"""
from __future__ import annotations

import inspect

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")

import dissmodel_ca.models as ca_models
from dissmodel.core import Environment
from dissmodel.geo import CellularAutomaton, raster_grid, vector_grid
from dissmodel.geo.raster.cellular_automaton import RasterCellularAutomaton

DIM, STEPS = 10, 5

# Models whose seeds sit at fixed positions of the canonical TerraME grid.
GRID = {"Excitable": 50, "Parity": 50}


def _concrete(base):
    return sorted(
        (name, cls)
        for name, cls in inspect.getmembers(ca_models, inspect.isclass)
        if issubclass(cls, base) and cls is not base and not inspect.isabstract(cls)
    )


VECTOR_MODELS = _concrete(CellularAutomaton)
RASTER_MODELS = _concrete(RasterCellularAutomaton)


def test_every_exported_model_is_covered():
    exported = {n for n in ca_models.__all__ if inspect.isclass(getattr(ca_models, n))}
    models = {n for n, c in inspect.getmembers(ca_models, inspect.isclass)
              if issubclass(c, (CellularAutomaton, RasterCellularAutomaton))}
    assert models <= exported
    assert len(VECTOR_MODELS) + len(RASTER_MODELS) == len(models) > 0


@pytest.mark.parametrize("name, cls", VECTOR_MODELS, ids=[n for n, _ in VECTOR_MODELS])
def test_vector_model_runs(name, cls):
    np.random.seed(0)
    env = Environment(start_time=0, end_time=STEPS)
    if name == "Wolfram":
        # one row per generation: xdim columns × (final_time + 1) rows
        xdim, final_time = 21, STEPS
        gdf = vector_grid(dimension=(xdim, final_time + 1), resolution=1, attrs={"state": 0})
        model = cls(gdf=gdf, xdim=xdim, final_time=final_time)
        n_cells = xdim * (final_time + 1)
    else:
        dim = GRID.get(name, DIM)
        gdf = vector_grid(dimension=(dim, dim), resolution=1, attrs={"state": 0})
        model = cls(gdf=gdf, dim=dim, start_time=0, end_time=STEPS)
        n_cells = dim * dim
    model.initialize()
    env.run()
    assert len(gdf) == n_cells          # no rows appended
    assert gdf.geometry.notna().all()
    assert np.isfinite(np.asarray(gdf["state"], dtype=float)).all()


@pytest.mark.parametrize("name, cls", RASTER_MODELS, ids=[n for n, _ in RASTER_MODELS])
def test_raster_model_runs(name, cls):
    np.random.seed(0)
    backend = raster_grid(rows=DIM, cols=DIM, attrs={"state": 0})
    env = Environment(start_time=0, end_time=STEPS)
    model = cls(backend=backend)
    if hasattr(model, "initialize"):
        model.initialize()
    env.run()
    state = backend.get("state")
    assert state.shape == (DIM, DIM)
    assert np.isfinite(state.astype(float)).all()


@pytest.mark.parametrize("name", sorted(GRID))
def test_seeded_models_reject_small_grid(name):
    """Seeds outside the grid raise instead of appending geometry-less rows."""
    cls = getattr(ca_models, name)
    Environment(start_time=0, end_time=STEPS)
    gdf = vector_grid(dimension=(DIM, DIM), resolution=1, attrs={"state": 0})
    model = cls(gdf=gdf, dim=DIM)
    with pytest.raises(ValueError, match="outside the grid"):
        model.initialize()
    assert len(gdf) == DIM * DIM


def test_wolfram_rejects_grid_smaller_than_its_dimensions():
    """Default final_time=55 needs 111 × 56; a 20 × 20 grid must raise."""
    Environment(start_time=0, end_time=STEPS)
    gdf = vector_grid(dimension=(DIM, DIM), resolution=1, attrs={"state": 0})
    model = ca_models.Wolfram(gdf=gdf)
    with pytest.raises(ValueError, match="Wolfram needs a grid"):
        model.initialize()
    assert len(gdf) == DIM * DIM
