from __future__ import annotations

import random
from enum import IntEnum
from typing import Any

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


def _queen_neighbors(idx: str, dim: int) -> list[str]:
    """
    Return the Moore (Queen) neighbor indices for a cell on a square grid.

    Computes neighbors directly from the ``"{y}-{x}"`` index format,
    clipping at grid boundaries (no wrap).

    Parameters
    ----------
    idx : str
        Cell index in ``"{y}-{x}"`` format.
    dim : int
        Grid side length (number of rows = number of columns).

    Returns
    -------
    list[str]
        Indices of valid neighbors (up to 8).
    """
    x, y = parse_idx(idx)
    neighbors = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < dim and 0 <= ny < dim:
                neighbors.append(f"{ny}-{nx}")
    return neighbors


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
    Because diffusion requires atomic swaps (two cells updated in a single
    operation), synchronous CA update is physically incorrect here — it
    would create or destroy atoms. :meth:`execute` therefore uses a
    **sequential random sweep**: vacancies are processed in a shuffled
    order, each swapping with one randomly chosen non-vacant neighbor.
    This matches the intended stochastic diffusion dynamics.

    Neighbor indices are computed directly from the ``"{y}-{x}"`` grid
    index format via :func:`_queen_neighbors`, avoiding reliance on any
    internal weights attribute.

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
            Random seed for the sequential shuffle in :meth:`execute`,
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
            x, _ = parse_idx(idx)
            if x < middle:
                return int(SolidDiffusionState.ATOM1)
            if x > middle:
                return int(SolidDiffusionState.ATOM2)
            return int(SolidDiffusionState.VACANCY)

        self.gdf["state"] = self.gdf.index.map(assign)

    def execute(self) -> None:
        """
        Perform one diffusion step via a sequential random vacancy sweep.

        Each vacancy in a randomly shuffled order picks one non-vacant
        neighbor at random and swaps states with it. Vacancies that have
        already been filled earlier in the same sweep are skipped.

        Neighbor indices are computed directly from grid indices using
        :func:`_queen_neighbors` — no spatial weights object required.
        """
        assert self.dim is not None, "dim must be set — pass dim=N when instantiating"

        indices = list(self.gdf.index)
        self._rng.shuffle(indices)

        for idx in indices:
            if self.gdf.loc[idx, "state"] != int(SolidDiffusionState.VACANCY):
                continue

            neighbor_ids = _queen_neighbors(idx, self.dim)
            non_vacant = [
                n for n in neighbor_ids
                if self.gdf.loc[n, "state"] != int(SolidDiffusionState.VACANCY)
            ]

            if not non_vacant:
                continue

            chosen = self._rng.choice(non_vacant)
            self.gdf.loc[idx,     "state"] = self.gdf.loc[chosen, "state"]
            self.gdf.loc[chosen,  "state"] = int(SolidDiffusionState.VACANCY)

    def rule(self, idx: Any) -> int:  # pragma: no cover
        """Not used. Diffusion logic is in :meth:`execute`."""
        raise NotImplementedError("SolidDiffusion uses execute() directly.")


__all__ = ["SolidDiffusion", "SolidDiffusionState"]
