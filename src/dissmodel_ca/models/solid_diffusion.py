from __future__ import annotations

import random
from enum import IntEnum
from typing import Any

import numpy as np
from dissmodel.geo import CellularAutomaton, parse_idx


class SolidDiffusionState(IntEnum):
    """
    Possible states for a cell in :class:`SolidDiffusion`.

    Attributes
    ----------
    ATOM1 : int
        First atom type (left half of the crystal, value 0).
    ATOM2 : int
        Second atom type (right half of the crystal, value 1).
    VACANCY : int
        Empty lattice site; atoms migrate through vacancies (value 2).
    """
    ATOM1   = 0
    ATOM2   = 1
    VACANCY = 2


#: (d_row, d_col) offsets of the Moore neighborhood, without wrap (TerraME default).
_MOORE: tuple[tuple[int, int], ...] = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)


class SolidDiffusion(CellularAutomaton):
    """
    Cellular automaton simulating atomic diffusion via the vacancy mechanism.

    Two types of atoms (``ATOM1`` and ``ATOM2``) are placed on opposite
    sides of a crystal lattice, separated by a column of vacancies in the
    middle. At each step, each vacancy randomly selects a non-vacant
    neighbor and swaps states with it, driving diffusion from high to low
    concentration regions until the crystal reaches uniform mixing.

    Based on the NetLogo Solid Diffusion model:
    http://ccl.northwestern.edu/netlogo/models/SolidDiffusion.
    Original implementation by Yasmine and John, Erasmus Mundus /
    Münster University, 2014.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame with geometries and a ``state`` attribute.
        Should be created with ``dimension=(dim, dim)`` (square grid).
    **kwargs :
        Extra keyword arguments forwarded to
        :class:`~dissmodel.geo.CellularAutomaton`.

    Notes
    -----
    The step follows the TerraME version (``ca`` package, ``SolidDiffusion``):

    - every cell reads the state at the start of the step (``cell.past``);
    - each cell that was a vacancy draws **one** of its Moore neighbors at
      random (a vacancy may draw another vacancy, and then stays put);
    - it takes the drawn atom, which becomes a vacancy, unless that atom
      was a vacancy at the start of the step or has already been taken by
      another vacancy in this step.

    So a vacancy moves at most once per step, and a vacancy created in the
    step does not move until the next one. Cells are visited in TerraME's
    order (column by column, and row by row within a column). The swaps
    keep the number of atoms of each kind.

    Examples
    --------
    >>> from dissmodel.geo import vector_grid
    >>> from dissmodel.core import Environment
    >>> gdf = vector_grid(dimension=(31, 31), resolution=1, attrs={"state": 0})
    >>> env = Environment(end_time=400)
    >>> sd = SolidDiffusion(gdf=gdf, dim=31)
    >>> sd.initialize()
    """

    def setup(self, seed: int = 42) -> None:
        """
        Configure the model.

        Parameters
        ----------
        seed : int, optional
            Random seed for the neighbor draws in :meth:`execute`,
            by default 42.
        """
        self.seed = seed
        self._rng = random.Random(seed)

    def initialize(self) -> None:
        """
        Set up the two-solid initial configuration.

        The grid is split vertically into three zones by column (x):

        - x < middle column → ``ATOM1`` (0)
        - x > middle column → ``ATOM2`` (1)
        - x == middle column → ``VACANCY`` (2)

        This creates a sharp interface at the centre of the crystal,
        matching the original TerraME model on a square grid.
        """
        assert self.dim is not None, "dim must be set — pass dim=N when instantiating"
        middle = self.dim // 2

        def assign(idx: str) -> int:
            _, y = parse_idx(idx)
            if y < middle:
                return int(SolidDiffusionState.ATOM1)
            if y > middle:
                return int(SolidDiffusionState.ATOM2)
            return int(SolidDiffusionState.VACANCY)

        self.gdf["state"] = self.gdf.index.map(assign)

    def execute(self) -> None:
        """
        Perform one diffusion step with TerraME's rule (see the class notes).
        """
        assert self.dim is not None, "dim must be set — pass dim=N when instantiating"

        index = list(self.gdf.index)
        pos = [parse_idx(i) for i in index]
        n_rows = max(p.row for p in pos) + 1
        n_cols = max(p.col for p in pos) + 1
        rows = np.array([p.row for p in pos])
        cols = np.array([p.col for p in pos])

        past = np.empty((n_rows, n_cols), dtype=np.int64)
        past[rows, cols] = self.gdf["state"].to_numpy()
        cur = past.copy()
        vacancy = int(SolidDiffusionState.VACANCY)

        # TerraME visits the cells column by column (x outer, y inner)
        for c in range(n_cols):
            for r in range(n_rows):
                if past[r, c] != vacancy:
                    continue
                neighbors = [
                    (r + dr, c + dc)
                    for dr, dc in _MOORE
                    if 0 <= r + dr < n_rows and 0 <= c + dc < n_cols
                ]
                nr, nc = neighbors[self._rng.randrange(len(neighbors))]
                if past[nr, nc] != vacancy and cur[nr, nc] != vacancy:
                    cur[r, c] = past[nr, nc]
                    cur[nr, nc] = vacancy

        self.gdf["state"] = cur[rows, cols]

    def rule(self, idx: Any) -> int:  # pragma: no cover
        """Not used. Diffusion logic is in :meth:`execute`."""
        raise NotImplementedError("SolidDiffusion uses execute() directly.")


__all__ = ["SolidDiffusion", "SolidDiffusionState"]
