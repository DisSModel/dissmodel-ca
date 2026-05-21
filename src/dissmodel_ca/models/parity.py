from __future__ import annotations

from enum import IntEnum
from typing import Any

from libpysal.weights import Rook

from dissmodel.geo import CellularAutomaton


class ParityState(IntEnum):
    """
    Possible states for a cell in :class:`Parity`.

    Attributes
    ----------
    OFF : int
        Inactive cell (0).
    ON : int
        Active cell (1).
    """
    OFF = 0
    ON  = 1


class Parity(CellularAutomaton):
    """
    Cellular automaton implementing the Parity rule (Gilbert).

    A cell turns ``ON`` if it has exactly 1 or 3 ``ON`` neighbors
    (Von Neumann neighborhood), and turns ``OFF`` otherwise.
    Starting from two isolated ``ON`` seeds, the rule produces
    expanding diamond-shaped wave patterns.

    Based on: Nigel Gilbert, modelingcommons.org/browse/one_model/3381.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame with geometries and a ``state`` attribute.
        Requires ``dim=50`` (or any square grid) when instantiating.
    **kwargs :
        Extra keyword arguments forwarded to
        :class:`~dissmodel.geo.CellularAutomaton`.

    Notes
    -----
    The canonical TerraME version uses a wrapped (toroidal) Von Neumann
    neighborhood. Boundary effects may differ slightly without wrapping.

    Examples
    --------
    >>> from dissmodel.geo import vector_grid
    >>> from dissmodel.core import Environment
    >>> gdf = vector_grid(dimension=(50, 50), resolution=1, attrs={"state": 0})
    >>> env = Environment(end_time=500)
    >>> parity = Parity(gdf=gdf, dim=50)
    >>> parity.initialize()
    """

    def setup(self) -> None:
        """Build the Rook (Von Neumann, 4-direction) neighborhood."""
        self.create_neighborhood(strategy=Rook, use_index=True)

    def initialize(self) -> None:
        """
        Place two ``ON`` seed cells at the canonical starting positions.

        Seeds at grid positions (x=10, y=25) and (x=40, y=25),
        matching the original TerraME model on a 50×50 grid.
        All other cells start as ``OFF``.
        """
        self.gdf["state"] = ParityState.OFF
        # TerraME (x, y) → DisSModel index "{y}-{x}"
        self.gdf.loc["25-10", "state"] = ParityState.ON
        self.gdf.loc["25-40", "state"] = ParityState.ON

    def rule(self, idx: Any) -> int:
        """
        Apply the Parity transition rule to cell ``idx``.

        Parameters
        ----------
        idx : any
            Index of the cell being evaluated.

        Returns
        -------
        int
            ``ON`` if the count of ``ON`` neighbors is 1 or 3;
            ``OFF`` otherwise.
        """
        count = (
            self.neighbor_values(idx, self.state_attr) == ParityState.ON
        ).sum()

        return ParityState.ON if count in (1, 3) else ParityState.OFF


__all__ = ["Parity", "ParityState"]
