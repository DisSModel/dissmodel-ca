from __future__ import annotations

import random
from enum import IntEnum
from typing import Any

from libpysal.weights import Rook

from dissmodel.geo import CellularAutomaton


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


class FireModel(CellularAutomaton):
    """
    Spatial cellular automaton simulating forest fire spread.

    The fire spreads to any forest cell that has at least one burning
    neighbor (Rook neighborhood — 4 cardinal directions).

    The default setup follows the TerraME ``Fire`` model of the ``ca``
    package: each cell is empty with probability :attr:`empty` (0.1) and
    forest otherwise, and a single cell, drawn at random among all cells,
    starts burning. Setting :attr:`initial_fire_density` above zero
    replaces the single ignition with a random fraction of burning cells.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame with geometries and a ``state`` attribute.
    **kwargs :
        Extra keyword arguments forwarded to
        :class:`~dissmodel.geo.CellularAutomaton`.

    Examples
    --------
    >>> from dissmodel.geo import vector_grid
    >>> from dissmodel.core import Environment
    >>> gdf = vector_grid(dimension=(10, 10), resolution=1, attrs={"state": 0})
    >>> env = Environment(end_time=10)
    >>> fire = FireModel(gdf=gdf)
    >>> fire.initialize()
    """

    #: Proportion of cells without vegetation (0.0 – 1.0).
    empty: float

    #: Proportion of cells initially on fire (0.0 – 1.0); 0 means a single ignition.
    initial_fire_density: float

    def setup(
        self,
        empty: float = 0.1,
        initial_fire_density: float = 0.0,
        seed: int = 42,
    ) -> None:
        """
        Configure the model and build the neighborhood.

        Parameters
        ----------
        empty : float, optional
            Probability that a cell starts empty (no vegetation), by
            default 0.1, as in TerraME. Must be between 0.0 and 1.0.
        initial_fire_density : float, optional
            Probability that a cell starts burning. With the default, 0.0,
            a single cell drawn at random among all cells starts burning,
            as in TerraME (``cs:sample().state = "burning"``).
        seed : int, optional
            Random seed used during initialization, by default 42.
        """
        self.empty = empty
        self.initial_fire_density = initial_fire_density
        self.seed = seed
        self.create_neighborhood(strategy=Rook, use_index=True)

    def initialize(self) -> None:
        """
        Fill the grid with a random initial state.

        Each cell is ``EMPTY`` with probability :attr:`empty` and
        ``FOREST`` otherwise. Then, if :attr:`initial_fire_density` is
        zero, one cell drawn among all cells (empty ones included, as in
        TerraME) is set to ``BURNING``; otherwise each cell is set to
        ``BURNING`` with probability :attr:`initial_fire_density`.
        """
        for name in ("empty", "initial_fire_density"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0, got {value}.")

        rng = random.Random(self.seed)
        state = [
            FireState.EMPTY if rng.random() < self.empty else FireState.FOREST
            for _ in range(len(self.gdf))
        ]
        if self.initial_fire_density > 0:
            state = [
                FireState.BURNING if rng.random() < self.initial_fire_density else s
                for s in state
            ]
        else:
            state[rng.randrange(len(state))] = FireState.BURNING
        self.gdf[self.state_attr] = [int(s) for s in state]

    def rule(self, idx: Any) -> int:
        """
        Apply the fire spread transition rule to cell ``idx``.

        Parameters
        ----------
        idx : any
            Index of the cell being evaluated.

        Returns
        -------
        int
            New state for the cell:

            - ``BURNED`` if the cell is currently burning.
            - ``BURNING`` if the cell is forest and has at least one
              burning neighbor.
            - Unchanged otherwise (``EMPTY`` and ``BURNED`` never change).
        """
        state = self.gdf.loc[idx, self.state_attr]

        if state == FireState.BURNING:
            return FireState.BURNED

        if state == FireState.FOREST:
            if (self.neighbor_values(idx, self.state_attr) == FireState.BURNING).any():
                return FireState.BURNING

        return state


__all__ = ["FireModel", "FireState"]