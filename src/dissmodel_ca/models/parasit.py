from __future__ import annotations

import random
from typing import Any

from libpysal.weights import Rook

from dissmodel.geo import CellularAutomaton


class Parasit(CellularAutomaton):
    """
    Cellular automaton implementing the host–parasite spatial dynamics model.

    Cells cycle through 9 states (0–8) representing the interleaved life
    cycles of a host and its parasite:

    - State 0 (susceptible host) → 1 if any neighbor is in state 1 (infectious).
    - States 1–2 (infected host): advance automatically (1→2→3).
    - State 3 (latent parasite) → 4 if any neighbor is in state 5 (mature parasite).
    - States 4–8 (parasite cycle): advance automatically (4→5→6→7→8→0).

    The two interacting waves produce complex spatiotemporal patterns
    characteristic of host–parasite coexistence.

    Based on: Hassell et al. (1991), *Spatial structure and chaos in
    insect population dynamics*, Nature, 353, 255–258.

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
    >>> gdf = vector_grid(dimension=(50, 50), resolution=1, attrs={"state": 0})
    >>> env = Environment(end_time=500)
    >>> parasit = Parasit(gdf=gdf)
    >>> parasit.initialize()
    """

    def setup(self, seed: int = 42) -> None:
        """
        Configure the model and build the neighborhood.

        Parameters
        ----------
        seed : int, optional
            Random seed for initialization, by default 42.
        """
        self.seed = seed
        self.create_neighborhood(strategy=Rook, use_index=True)

    def initialize(self) -> None:
        """
        Fill the grid with a random initial state.

        Each cell is assigned a random integer state in [0, 8],
        producing a mixed starting configuration from which the
        host–parasite wave interaction can develop.
        """
        rng = random.Random(self.seed)
        self.gdf["state"] = [rng.randint(0, 8) for _ in range(len(self.gdf))]

    def rule(self, idx: Any) -> int:
        """
        Apply the host–parasite transition rule to cell ``idx``.

        Parameters
        ----------
        idx : any
            Index of the cell being evaluated.

        Returns
        -------
        int
            New state (0–8) according to the host–parasite cycle.
        """
        state = self.gdf.loc[idx, self.state_attr]
        neighbors = self.neighbor_values(idx, self.state_attr)

        if state == 0:
            return 1 if (neighbors == 1).any() else 0
        if state == 1:
            return 2
        if state == 2:
            return 3
        if state == 3:
            return 4 if (neighbors == 5).any() else 3
        if state == 4:
            return 5
        if state == 5:
            return 6
        if state == 6:
            return 7
        if state == 7:
            return 8
        # state == 8
        return 0


__all__ = ["Parasit"]
