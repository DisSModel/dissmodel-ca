from __future__ import annotations

from enum import IntEnum
from typing import Any

from dissmodel.geo import CellularAutomaton

from ._neighborhood import grid_neighbors


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
    As in the TerraME version (``createNeighborhood{strategy =
    "vonneumann", wrap = true}``), the neighborhood wraps around the grid
    edges (torus), so the waves re-enter on the opposite side instead of
    stopping at the border. Pass ``wrap=False`` for a bounded grid.

    Examples
    --------
    >>> from dissmodel.geo import vector_grid
    >>> from dissmodel.core import Environment
    >>> gdf = vector_grid(dimension=(50, 50), resolution=1, attrs={"state": 0})
    >>> env = Environment(end_time=500)
    >>> parity = Parity(gdf=gdf, dim=50)
    >>> parity.initialize()
    """

    def setup(self, wrap: bool = True) -> None:
        """
        Build the Von Neumann (4-direction) neighborhood.

        Parameters
        ----------
        wrap : bool, optional
            If ``True`` (default, as in TerraME), opposite edges of the
            grid are neighbors (toroidal grid).
        """
        self.wrap = wrap
        self.create_neighborhood(
            neighbors_dict=grid_neighbors(self.gdf.index, "vonneumann", wrap=wrap)
        )

    def initialize(self) -> None:
        """
        Place two ``ON`` seed cells at the canonical starting positions.

        Seeds at grid positions (x=10, y=25) and (x=40, y=25),
        matching the original TerraME model on a 50×50 grid.
        All other cells start as ``OFF``.
        """
        # TerraME (x, y) → DisSModel index "{y}-{x}" (row y counted from the
        # bottom, so the map is the TerraME map flipped vertically)
        seeds = ["25-10", "25-40"]
        missing = [s for s in seeds if s not in self.gdf.index]
        if missing:
            # .loc on a missing label would silently append geometry-less rows
            raise ValueError(
                f"Parity seeds {missing} are outside the grid: it needs at least "
                "41 columns × 26 rows (the canonical setup is 50×50)."
            )
        self.gdf["state"] = ParityState.OFF
        self.gdf.loc[seeds, "state"] = ParityState.ON

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
