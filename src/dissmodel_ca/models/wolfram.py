from __future__ import annotations

from typing import Any

from dissmodel.geo import CellularAutomaton


def _build_rule_table(rule_number: int) -> dict[str, int]:
    """
    Convert a Wolfram rule number (0–255) to a lookup table.

    Maps each 3-bit neighborhood pattern (e.g. ``"110"``) to its
    output bit according to the elementary CA rule encoding.

    Parameters
    ----------
    rule_number : int
        Rule number from 0 to 255 (Wolfram convention).

    Returns
    -------
    dict[str, int]
        Mapping from 3-bit pattern string to output state (0 or 1).
    """
    bits = format(rule_number, "08b")  # MSB first, e.g. rule 90 → "01011010"
    patterns = ["111", "110", "101", "100", "011", "010", "001", "000"]
    return {p: int(b) for p, b in zip(patterns, bits)}


class Wolfram(CellularAutomaton):
    """
    Cellular automaton implementing Wolfram's elementary (1D) rules.

    The 1D automaton is displayed in 2D: each row stores one generation.
    Row 0 holds the initial state (single alive cell at the center).
    At each step *t*, row *t* is filled from row *t − 1* using a
    3-cell neighborhood and the selected rule table.

    The grid must be created with::

        vector_grid(dimension=(2 * final_time + 1, final_time + 1))

    where ``dimension=(xdim, ydim)`` and ``xdim`` is the number of
    columns, ``ydim`` the number of rows (generations).

    Based on: http://mathworld.wolfram.com/ElementaryCellularAutomaton.html.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame with geometries and a ``state`` attribute.
        Must match the required dimensions described above.
    **kwargs :
        Extra keyword arguments forwarded to
        :class:`~dissmodel.geo.CellularAutomaton`.

    Notes
    -----
    Because Wolfram CAs advance row by row (not cell by cell),
    :meth:`execute` is fully overridden. :meth:`rule` is not used.

    The neighborhood wraps horizontally: the leftmost and rightmost
    cells in each row treat the opposite edge as their neighbor.

    Examples
    --------
    >>> from dissmodel.geo import vector_grid
    >>> from dissmodel.core import Environment
    >>> final_time = 55
    >>> gdf = vector_grid(
    ...     dimension=(2 * final_time + 1, final_time + 1),
    ...     resolution=1,
    ...     attrs={"state": 0},
    ... )
    >>> env = Environment(end_time=final_time)
    >>> wolfram = Wolfram(gdf=gdf, rule_number=90, final_time=final_time)
    >>> wolfram.initialize()
    """

    def setup(
        self,
        rule_number: int = 90,
        final_time: int = 55,
    ) -> None:
        """
        Configure the model.

        Parameters
        ----------
        rule_number : int, optional
            Wolfram elementary rule number from 0 to 255, by default 90.
            Rule 90 produces a Sierpiński triangle pattern.
        final_time : int, optional
            Number of generations (rows). Must match the ``ydim`` used
            when creating the GeoDataFrame, by default 55.

        Raises
        ------
        ValueError
            If ``rule_number`` is not in the range [0, 255].
        """
        if not 0 <= rule_number <= 255:
            raise ValueError(f"rule_number must be between 0 and 255, got {rule_number}.")
        self.rule_number = rule_number
        self.final_time  = final_time
        self.xdim        = 2 * final_time + 1  # number of columns
        self._rule_table = _build_rule_table(rule_number)

    def initialize(self) -> None:
        """
        Set a single alive cell at the center of row 0.

        All other cells start as dead (0). The center column is
        ``floor((xdim + 1) / 2 - 1)`` — the same formula used in
        the original TerraME implementation.
        """
        self.gdf[self.state_attr] = 0
        mid = (self.xdim + 1) // 2 - 1
        self.gdf.loc[f"0-{mid}", self.state_attr] = 1

    def execute(self) -> None:
        """
        Fill the current generation row from the previous one.

        At simulation time *t*, reads row *t − 1* and writes row *t*
        by applying the rule table to each 3-cell neighborhood.
        Horizontal boundaries wrap (toroidal).

        Steps t=0 and t > final_time are skipped: row 0 is already
        set by :meth:`initialize`, and no rows exist beyond the grid.
        """
        t = int(self.env.now())
        if t == 0 or t > self.final_time:
            return
        yc = t - 1  # source row (previous generation)
        yn = t      # destination row (current generation)

        for x in range(self.xdim):
            left  = (x - 1) % self.xdim
            right = (x + 1) % self.xdim

            topl = int(self.gdf.loc[f"{yc}-{left}",  self.state_attr])
            topc = int(self.gdf.loc[f"{yc}-{x}",     self.state_attr])
            topr = int(self.gdf.loc[f"{yc}-{right}", self.state_attr])

            conf = f"{topl}{topc}{topr}"
            self.gdf.loc[f"{yn}-{x}", self.state_attr] = self._rule_table[conf]

    def rule(self, idx: Any) -> int:  # pragma: no cover
        """Not used. Row-based logic is in :meth:`execute`."""
        raise NotImplementedError("Wolfram uses execute() directly.")


__all__ = ["Wolfram"]
