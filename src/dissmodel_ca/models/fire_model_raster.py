"""
dissmodel_ca.models.py
========================================
Raster version of FireModel using RasterCellularAutomaton.

Symmetric counterpart of FireModel (GeoDataFrame + CellularAutomaton).
Same logic, different substrate — rule() operates on the full NumPy
grid in one vectorized call instead of cell-by-cell.

Comparison
----------
    # vector — rule called once per cell per step
    class FireModel(CellularAutomaton):
        def rule(self, idx):
            state = self.gdf.loc[idx, self.state_attr]
            if state == BURNING: return BURNED
            if state == FOREST:
                if (self.neighbor_values(idx, "state") == BURNING).any():
                    return BURNING
            return state

    # raster — rule called once per step, covers all cells
    class FireModel(RasterCellularAutomaton):
        def rule(self, arrays):
            state        = arrays["state"]
            has_burning  = self.backend.focal_sum_mask(state == BURNING) > 0
            new_state    = np.where(state == BURNING, BURNED, state)
            new_state    = np.where((state == FOREST) & has_burning, BURNING, new_state)
            return {"state": new_state}

Usage
-----
    from dissmodel.core import Environment
    from dissmodel.geo.raster.backend import RasterBackend
    from dissmodel_ca.models import FireModel
    import numpy as np

    b = RasterBackend(shape=(50, 50))
    rng = np.random.default_rng(42)
    state = np.where(rng.random((50, 50)) < 0.05, FireState.BURNING, FireState.FOREST)
    b.set("state", state.astype(np.int8))

    env = Environment(start_time=1, end_time=30)
    FireModel(backend=b)
    env.run()
"""
from __future__ import annotations

from enum import IntEnum

import numpy as np

from dissmodel.geo.raster.backend import RasterBackend, DIRS_VON_NEUMANN
from dissmodel.geo import RasterCellularAutomaton


class FireState(IntEnum):
    """
    Possible states for a cell in :class:`FireModel`.

    Attributes
    ----------
    FOREST : int
        Healthy tree, can catch fire.
    BURNING : int
        Actively burning, spreads fire to neighbors.
    BURNED : int
        Already burned, no longer spreads.
    EMPTY : int
        No vegetation; never burns. Its code comes after the others so
        that the codes 0–2 keep their earlier meaning.
    """
    FOREST  = 0
    BURNING = 1
    BURNED  = 2
    EMPTY   = 3


class FireModel(RasterCellularAutomaton):
    """
    Raster cellular automaton simulating forest fire spread.

    Symmetric counterpart of the vector FireModel — same state machine,
    same Rook (Von Neumann, 4-direction) neighborhood, fully vectorized.

    The fire spreads to any FOREST cell that has at least one BURNING
    neighbor. BURNING cells become BURNED in the next step.

    Parameters
    ----------
    backend : RasterBackend
        Shared backend. Must contain a ``"state"`` array (or the name
        set via ``state_attr``) with values from :class:`FireState`.
    empty : float, optional
        Probability that a cell starts EMPTY, by default 0.1 (as in the
        TerraME ``Fire`` model). Only used if ``initialize()`` is called.
    initial_fire_density : float, optional
        Probability that a cell starts BURNING. With the default, 0.0, a
        single cell drawn among all cells starts burning, as in TerraME.
        Only used if ``initialize()`` is called.
    seed : int, optional
        Random seed for initialization, by default 42.
    state_attr : str, optional
        Name of the state array in the backend, by default ``"state"``.

    Examples
    --------
    >>> from dissmodel.core import Environment
    >>> from dissmodel.geo.raster.backend import RasterBackend
    >>> import numpy as np
    >>> b = RasterBackend(shape=(20, 20))
    >>> rng = np.random.default_rng(42)
    >>> state = np.where(rng.random((20, 20)) < 0.05, FireState.BURNING, FireState.FOREST)
    >>> b.set("state", state.astype(np.int8))
    >>> env = Environment(start_time=1, end_time=20)
    >>> FireModel(backend=b)
    """

    def setup(
        self,
        backend:              RasterBackend,
        empty:                float = 0.1,
        initial_fire_density: float = 0.0,
        seed:                 int   = 42,
        state_attr:           str   = "state",
    ) -> None:
        super().setup(backend, state_attr=state_attr)
        self.empty                = empty
        self.initial_fire_density = initial_fire_density
        self.seed                 = seed
        # Rook = Von Neumann (4 directions) — same as vector FireModel
        self.dirs = DIRS_VON_NEUMANN

    def initialize(self) -> None:
        """
        Fill the grid with a random initial state.

        Each cell is EMPTY with probability :attr:`empty` and FOREST
        otherwise. Then, if :attr:`initial_fire_density` is zero, one cell
        drawn among all cells (empty ones included, as in TerraME) is set
        to BURNING; otherwise each cell is set to BURNING with probability
        :attr:`initial_fire_density`. Only needed when the backend array
        is not already initialized.
        """
        for name in ("empty", "initial_fire_density"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0, got {value}.")

        rng   = np.random.default_rng(self.seed)
        state = np.where(
            rng.random(self.shape) < self.empty,
            int(FireState.EMPTY),
            int(FireState.FOREST),
        ).astype(np.int8)
        if self.initial_fire_density > 0:
            state[rng.random(self.shape) < self.initial_fire_density] = int(FireState.BURNING)
        else:
            state.flat[rng.integers(state.size)] = int(FireState.BURNING)
        self.backend.set(self.state_attr, state)

    def rule(self, arrays: dict) -> dict:
        """
        Vectorized fire spread transition rule.

        Applied once per step over the entire grid:

        - BURNING → BURNED
        - FOREST with ≥ 1 BURNING neighbor → BURNING  (Rook neighborhood)
        - otherwise → unchanged (EMPTY and BURNED never change)

        Parameters
        ----------
        arrays : dict[str, np.ndarray]
            Snapshot of backend arrays (past state).

        Returns
        -------
        dict[str, np.ndarray]
            Updated ``"state"`` array.
        """
        state = arrays[self.state_attr]

        # count BURNING neighbors (Von Neumann / Rook — 4 directions)
        has_burning = self.backend.focal_sum_mask(
            state == int(FireState.BURNING), self.dirs
        ) > 0

        new_state = state.copy()
        new_state = np.where(state == int(FireState.BURNING), int(FireState.BURNED),  new_state)
        new_state = np.where((state == int(FireState.FOREST)) & has_burning, int(FireState.BURNING), new_state)

        return {self.state_attr: new_state.astype(np.int8)}
