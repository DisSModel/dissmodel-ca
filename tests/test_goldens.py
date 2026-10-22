"""
The models against TerraME itself.

``goldens/`` holds an extract of the ``ca`` suite of ``terrame-goldens``: what
TerraME 2.0.1 computed running the models of the ``ca`` package (see
``goldens/README.md``). Two kinds of tests:

- **Grids**: models whose rule is deterministic start from TerraME's state at
  step 0 and must match it **cell by cell** at every step kept in the
  extract.
- **Ensembles**: models that draw random numbers while they run are compared
  by distribution. At each step kept, the number of cells in each state over
  ``SEEDS`` runs and over TerraME's 50 runs must pass a two-sample
  Kolmogorov-Smirnov test (p >= ``P_MIN``) and their means must not differ by
  more than ``Z_MAX`` standard errors.

The vector models take 0.2 to 2 s per step, so by default the grids are
compared over the first ``QUICK_STEPS`` steps (the raster models and Wolfram
over all of them) and only the fast ensembles run, in about a minute. Set
``DISSMODEL_GOLDEN_FULL=1`` to compare every step kept and every ensemble
(Growth alone takes hours).
"""
from __future__ import annotations

import csv
import gzip
import json
import os
import random
from collections import defaultdict
from collections.abc import Callable
from functools import cache
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from dissmodel.core import Environment, Model
from dissmodel.geo import parse_idx, vector_grid
from dissmodel.geo.raster.backend import RasterBackend

import dissmodel_ca.models as ca

pytestmark = pytest.mark.golden

GOLDENS = Path(__file__).resolve().parent / "goldens"
REFERENCE = json.loads((GOLDENS / "reference.json").read_text())
FULL = os.environ.get("DISSMODEL_GOLDEN_FULL", "") not in ("", "0")
QUICK_STEPS = 10
SEEDS = range(1, 21)
Z_MAX = 4.0
P_MIN = 0.001


# -- grids ---------------------------------------------------------------------------------


def load_grid(case: str) -> dict[int, np.ndarray]:
    """``{step: (y, x) array of TerraME's values as str}``."""
    with gzip.open(GOLDENS / "grids" / f"{case}.csv.gz", "rt", newline="") as f:
        rows = list(csv.reader(f))
    nx = len(rows[0]) - 2
    by_step: dict[int, dict[int, list[str]]] = defaultdict(dict)
    for r in rows[1:]:
        by_step[int(r[0])][int(r[1])] = r[2:]
    return {
        t: np.array([g[y] for y in range(len(g))], dtype=object).reshape(len(g), nx)
        for t, g in by_step.items()
    }


class _Recorder(Model):
    """Reads the model after each step listed (created after the model, so it runs after it)."""

    def setup(self, read: Callable[[], Any], steps: set[int]) -> None:  # type: ignore[override]
        self.read, self.steps, self.frames = read, steps, {}

    def execute(self) -> None:
        t = int(self.env.now())
        if t in self.steps:
            self.frames[t] = self.read()


def run_vector(factory: Callable[[Any], Any], init: np.ndarray, steps: set[int]) -> dict[int, np.ndarray]:
    ny, nx = init.shape
    env = Environment(start_time=1, end_time=max(steps))
    gdf = vector_grid(dimension=(nx, ny), resolution=1, attrs={"state": 0})
    model = factory(gdf)
    pos = [parse_idx(i) for i in model.gdf.index]
    rows = np.array([p.row for p in pos])
    cols = np.array([p.col for p in pos])
    model.gdf["state"] = init[rows, cols]

    def read() -> np.ndarray:
        out = np.zeros((ny, nx), dtype=int)
        out[rows, cols] = model.gdf["state"].to_numpy()
        return out

    rec = _Recorder(read=read, steps=steps)
    env.run()
    return rec.frames


def run_raster(factory: Callable[[Any], Any], init: np.ndarray, steps: set[int]) -> dict[int, np.ndarray]:
    env = Environment(start_time=1, end_time=max(steps))
    backend = RasterBackend(shape=init.shape)
    backend.set("state", init.astype(np.int8))
    factory(backend)
    rec = _Recorder(read=lambda: backend.arrays["state"].astype(int).copy(), steps=steps)
    env.run()
    return rec.frames


LIFE = {"dead": 0, "alive": 1}
FIRE = {"forest": 0, "burning": 1, "burned": 2, "empty": 3}

#: id, golden, values -> codes (None: integers), runner, factory, quick (compare every step by default)
GRID_CASES = [
    ("life_glider", "life_glider", LIFE, run_vector, lambda g: ca.GameOfLife(gdf=g), False),
    ("life_rpentomino", "life_rpentomino", LIFE, run_vector, lambda g: ca.GameOfLife(gdf=g), False),
    ("life_random", "life_random", LIFE, run_vector, lambda g: ca.GameOfLife(gdf=g), False),
    ("life_random-raster", "life_random", LIFE, run_raster,
     lambda b: ca.GameOfLifeRaster(backend=b), True),
    ("parity", "parity", {"off": 0, "on": 1}, run_vector, lambda g: ca.Parity(gdf=g, dim=50), False),
    ("excitable", "excitable", None, run_vector, lambda g: ca.Excitable(gdf=g, dim=50), False),
    ("wolfram_30", "wolfram_30", LIFE, run_vector, lambda g: ca.Wolfram(gdf=g, rule_number=30), True),
    ("wolfram_90", "wolfram_90", LIFE, run_vector, lambda g: ca.Wolfram(gdf=g, rule_number=90), True),
    ("wolfram_110", "wolfram_110", LIFE, run_vector, lambda g: ca.Wolfram(gdf=g, rule_number=110), True),
    ("fire", "fire", FIRE, run_vector, lambda g: ca.FireModel(gdf=g), False),
    ("fire-raster", "fire", FIRE, run_raster, lambda b: ca.FireModelRaster(backend=b), True),
    ("anneal", "anneal", {"L": 0, "R": 1}, run_vector, lambda g: ca.Anneal(gdf=g), False),
    ("oscillator", "oscillator", None, run_vector, lambda g: ca.Oscillator(gdf=g), False),
    ("parasit", "parasit", None, run_vector, lambda g: ca.Parasit(gdf=g), False),
]


def codes(grid: np.ndarray, mapping: dict[str, int] | None) -> np.ndarray:
    if mapping is None:
        return grid.astype(int)
    return np.vectorize(mapping.__getitem__, otypes=[int])(grid)


@pytest.mark.parametrize(
    "golden,mapping,runner,factory,quick",
    [c[1:] for c in GRID_CASES],
    ids=[c[0] for c in GRID_CASES],
)
def test_grid_matches_terrame_cell_by_cell(golden, mapping, runner, factory, quick) -> None:
    ref = {t: codes(g, mapping) for t, g in load_grid(golden).items()}
    steps = {t for t in ref if t > 0 and (FULL or quick or t <= QUICK_STEPS)}
    ours = runner(factory, ref[0], steps)
    for t in sorted(steps):
        diff = int((ours[t] != ref[t]).sum())
        assert diff == 0, f"{golden}: {diff} cells differ from TerraME at step {t}"


# -- ensembles -------------------------------------------------------------------------------


def ks_pvalue(a: np.ndarray, b: np.ndarray) -> float:
    """Two-sample Kolmogorov-Smirnov test, asymptotic p-value (Numerical Recipes ``kstwo``)."""
    grid = np.union1d(a, b)
    d = np.abs(
        np.searchsorted(np.sort(a), grid, side="right") / len(a)
        - np.searchsorted(np.sort(b), grid, side="right") / len(b)
    ).max()
    en = np.sqrt(len(a) * len(b) / (len(a) + len(b)))
    lam = (en + 0.12 + 0.11 / en) * d
    if lam < 1e-3:
        return 1.0
    k = np.arange(1, 101)
    return float(np.clip(2 * np.sum((-1.0) ** (k - 1) * np.exp(-2 * (k * lam) ** 2)), 0, 1))


@cache
def ensemble_reference() -> dict[tuple[str, str, int], np.ndarray]:
    values: dict[tuple[str, str, int], list[int]] = defaultdict(list)
    with gzip.open(GOLDENS / "ensembles.csv.gz", "rt", newline="") as f:
        for r in csv.DictReader(f):  # sorted by seed within (case, value, step)
            values[(r["case"], r["value"], int(r["step"]))].append(int(r["count"]))
    return {k: np.array(v) for k, v in values.items()}


Counts = dict[str, int]


def _counts(state: np.ndarray, mapping: dict[str, int]) -> Counts:
    return {value: int((state == code).sum()) for value, code in mapping.items()}


def _vector_ensemble(n: int, mapping: dict[str, int], factory: Callable[[Any, int], Any]):
    def run(seed: int, steps: set[int]) -> dict[int, Counts]:
        random.seed(seed)
        np.random.seed(seed)
        env = Environment(start_time=1, end_time=max(steps))
        gdf = vector_grid(dimension=(n, n), resolution=1, attrs={"state": 0})
        model = factory(gdf, seed)
        model.initialize()
        cols = np.array([parse_idx(i).col for i in model.gdf.index])

        def read() -> Counts:
            state = model.gdf["state"].to_numpy()
            out = _counts(state, mapping)
            if "atom1" in mapping:  # SolidDiffusion: atoms across the middle column
                middle = n // 2
                out["atom1_right"] = int(((state == mapping["atom1"]) & (cols > middle)).sum())
                out["atom2_left"] = int(((state == mapping["atom2"]) & (cols < middle)).sum())
            return out

        rec = _Recorder(read=read, steps=steps)
        env.run()
        return rec.frames
    return run


def _fire_raster(seed: int, steps: set[int]) -> dict[int, Counts]:
    env = Environment(start_time=1, end_time=max(steps))
    backend = RasterBackend(shape=(60, 60))
    model = ca.FireModelRaster(backend=backend, seed=seed)
    model.initialize()
    rec = _Recorder(read=lambda: _counts(backend.arrays["state"], FIRE), steps=steps)
    env.run()
    return rec.frames


SOLID = {"atom1": 0, "atom2": 1, "vacancy": 2}
SPECIES = {"Lolium": 0, "Agrostis": 1, "Holcus": 2, "Poa": 3, "Cynosurus": 4}

#: case -> (runner, runs by default). SolidDiffusion only swaps atoms, so its
#: counts per state never change; ``atom1_right`` and ``atom2_left`` (atoms
#: past the middle column) measure how far they mixed.
ENSEMBLES: dict[str, tuple[Callable[[int, set[int]], dict[int, Counts]], bool]] = {
    "fire": (_fire_raster, True),
    "solid_diffusion": (
        _vector_ensemble(31, SOLID, lambda g, s: ca.SolidDiffusion(gdf=g, dim=31, seed=s)), True),
    "growth": (
        _vector_ensemble(100, {"alive": 1, "empty": 0}, lambda g, s: ca.Growth(gdf=g, dim=100)), False),
    "snow": (
        _vector_ensemble(50, {"snow": 1, "empty": 0},
                         lambda g, s: ca.Snow(gdf=g, dim=50, end_time=600)), False),
    "interspecific_competition": (
        _vector_ensemble(40, SPECIES,
                         lambda g, s: ca.InterspecificCompetition(gdf=g, dim=40, seed=s)), False),
}


@cache
def ensemble_runs(case: str) -> dict[tuple[str, int], np.ndarray]:
    runner, _ = ENSEMBLES[case]
    steps = set(REFERENCE["ensemble_steps"][case])
    out: dict[tuple[str, int], list[int]] = defaultdict(list)
    for seed in SEEDS:
        for t, counts in runner(seed, steps).items():
            for value, count in counts.items():
                out[(value, t)].append(count)
    return {k: np.array(v) for k, v in out.items()}


ENSEMBLE_CASES = sorted(k for k in ensemble_reference() if k[0] in ENSEMBLES)


@pytest.mark.parametrize(
    "case,value,step", ENSEMBLE_CASES, ids=[f"{c}-{v}-t{s}" for c, v, s in ENSEMBLE_CASES]
)
def test_ensemble_matches_terrame(case: str, value: str, step: int) -> None:
    if not (FULL or ENSEMBLES[case][1]):
        pytest.skip("slow ensemble; set DISSMODEL_GOLDEN_FULL=1")
    tm = ensemble_reference()[(case, value, step)]
    ours = ensemble_runs(case)[(value, step)]
    se = np.sqrt(tm.var(ddof=1) / len(tm) + ours.var(ddof=1) / len(ours))
    diff = ours.mean() - tm.mean()
    p = ks_pvalue(tm, ours)
    msg = (f"{case} '{value}' at t={step}: TerraME {tm.mean():.1f} ± {tm.std():.1f}, "
           f"dissmodel-ca {ours.mean():.1f} ± {ours.std():.1f}, KS p = {p:.2g}")
    assert p >= P_MIN, msg
    if se > 0:
        assert abs(diff) <= Z_MAX * se, f"{msg}, z = {diff / se:.1f}"
    else:
        assert diff == 0, msg
