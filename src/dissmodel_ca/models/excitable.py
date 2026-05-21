from __future__ import annotations

from typing import Any

from libpysal.weights import Rook

from dissmodel.geo import CellularAutomaton


class Excitable(CellularAutomaton):
    """
    Cellular automaton implementing the Excitable medium rule.

    Cells cycle through 6 states (0–5). A resting cell (state ``0``)
    becomes excited (state ``1``) if it has at least one excited neighbor.
    Excited and refractory cells advance through states 1→2→3→4→5→0
    deterministically, creating outward-propagating spiral or ring waves.

    Based on: Wiener & Rosenbleuth (1946), as referenced in
    Ermentrout & Edelstein-Keshet (1993), *Cellular Automata Approaches
    to Biological Modeling*, Journal of Theoretical Biology, 160, 97–133.

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
    States 1–5 are refractory: they advance automatically and cannot be
    re-excited until they return to state 0. This refractory period
    prevents wave collision and produces clean propagation fronts.

    Examples
    --------
    >>> from dissmodel.geo import vector_grid
    >>> from dissmodel.core import Environment
    >>> gdf = vector_grid(dimension=(50, 50), resolution=1, attrs={"state": 0})
    >>> env = Environment(end_time=500)
    >>> exc = Excitable(gdf=gdf, dim=50)
    >>> exc.initialize()
    """

    def setup(self) -> None:
        """Build the Rook (Von Neumann, 4-direction) neighborhood."""
        self.create_neighborhood(strategy=Rook, use_index=True)

    def initialize(self) -> None:
        """
        Place two excited seed cells at the canonical starting positions.

        Seeds at grid positions (x=20, y=25) and (x=30, y=25),
        matching the original TerraME model on a 50×50 grid.
        All other cells start at state ``0`` (resting).
        """
        self.gdf["state"] = 0
        # TerraME (x, y) → DisSModel index "{y}-{x}"
        self.gdf.loc["15-20", "state"] = 1
        self.gdf.loc["15-30", "state"] = 1

    def rule(self, idx: Any) -> int:
        """
        Apply the Excitable transition rule to cell ``idx``.

        Parameters
        ----------
        idx : any
            Index of the cell being evaluated.

        Returns
        -------
        int
            New state (0–5):

            - State 0 (resting) → 1 if any neighbor is in state > 0,
              otherwise stays 0.
            - States 1–5 (excited/refractory) → advance by 1 modulo 6
              (i.e. 1→2, 2→3, 3→4, 4→5, 5→0).
        """
        state = self.gdf.loc[idx, self.state_attr]

        if state == 0:
            if (self.neighbor_values(idx, self.state_attr) > 0).any():
                return 1
            return 0

        # Refractory cycle: 1→2→3→4→5→0
        return (state + 1) % 6


__all__ = ["Excitable"]
