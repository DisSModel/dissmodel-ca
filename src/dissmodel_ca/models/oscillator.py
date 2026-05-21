from __future__ import annotations

import random
from typing import Any

from libpysal.weights import Queen

from dissmodel.geo import CellularAutomaton


# Amount table from Ermentrout & Edelstein-Keshet (1993).
# Index corresponds to cell state (0–15).
# Used when at least one neighbor is in state 0.
_AMOUNT: list[int] = [0, -1, -2, -2, -3, -2, -2, -1, 0, 1, 2, 2, 3, 2, 2, 1]


class Oscillator(CellularAutomaton):
    """
    Cellular automaton implementing the Oscillator rule.

    Cells hold an integer state in [0, 15]. At each step, the transition
    depends on whether any Moore neighbor is in state ``0``:

    - **Neighbor in state 0 present**: new state is
      ``(state + AMOUNT[state] + 1) % 16``, where ``AMOUNT`` is a
      predefined lookup table that creates non-uniform oscillation speeds.
    - **No neighbor in state 0**: new state is ``(state + 1) % 16``
      (simple counter increment).

    The interaction between cells in state 0 and their neighbors produces
    synchronized oscillating domains and complex wave-like patterns.

    Based on: Ermentrout & Edelstein-Keshet (1993), *Cellular Automata
    Approaches to Biological Modeling*, Journal of Theoretical Biology,
    160, 97–133.

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
    >>> env = Environment(end_time=400)
    >>> osc = Oscillator(gdf=gdf)
    >>> osc.initialize()
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
        self.create_neighborhood(strategy=Queen, use_index=True)

    def initialize(self) -> None:
        """
        Fill the grid with a random initial state.

        Each cell is assigned a random integer state in [0, 15].
        """
        rng = random.Random(self.seed)
        self.gdf["state"] = [rng.randint(0, 15) for _ in range(len(self.gdf))]

    def rule(self, idx: Any) -> int:
        """
        Apply the Oscillator transition rule to cell ``idx``.

        Parameters
        ----------
        idx : any
            Index of the cell being evaluated.

        Returns
        -------
        int
            New state in [0, 15]:

            - ``(state + AMOUNT[state] + 1) % 16`` if any Moore neighbor
              is in state 0.
            - ``(state + 1) % 16`` otherwise.
        """
        state = int(self.gdf.loc[idx, self.state_attr])
        neighbors = self.neighbor_values(idx, self.state_attr)

        if (neighbors == 0).any():
            return (state + _AMOUNT[state] + 1) % 16

        return (state + 1) % 16


__all__ = ["Oscillator"]
