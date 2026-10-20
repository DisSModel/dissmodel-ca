"""
Grid neighborhoods built from the ``"row-col"`` cell index.

libpysal's ``Rook`` and ``Queen`` find neighbors by shared geometry, so
they cannot express TerraME's ``createNeighborhood{wrap = true}``, in
which the grid closes on itself as a torus. :func:`grid_neighbors` builds
the same neighborhoods from the index of a grid made by
:func:`dissmodel.geo.vector_grid`, with or without wrapping, and returns
the mapping that :meth:`~dissmodel.geo.CellularAutomaton.create_neighborhood`
accepts as ``neighbors_dict``.
"""
from __future__ import annotations

from collections.abc import Iterable

from dissmodel.geo import parse_idx

#: (d_row, d_col) offsets of the 4-cell Von Neumann neighborhood (TerraME "vonneumann").
VON_NEUMANN: tuple[tuple[int, int], ...] = ((-1, 0), (0, -1), (0, 1), (1, 0))

#: (d_row, d_col) offsets of the 8-cell Moore neighborhood (TerraME default, "moore").
MOORE: tuple[tuple[int, int], ...] = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

_STRATEGIES = {"vonneumann": VON_NEUMANN, "moore": MOORE}


def grid_neighbors(
    index: Iterable[str],
    strategy: str = "vonneumann",
    wrap: bool = False,
) -> dict[str, list[str]]:
    """
    Build a ``{cell: [neighbors]}`` mapping for a rectangular grid.

    Parameters
    ----------
    index : iterable of str
        Cell labels in ``"row-col"`` format, as produced by
        :func:`dissmodel.geo.vector_grid`. The grid size is taken from the
        largest row and column found.
    strategy : {"vonneumann", "moore"}, optional
        4-cell (Von Neumann) or 8-cell (Moore) neighborhood, by default
        ``"vonneumann"``.
    wrap : bool, optional
        If ``True``, opposite edges are neighbors (toroidal grid), as in
        TerraME's ``createNeighborhood{wrap = true}``; by default ``False``.

    Returns
    -------
    dict[str, list[str]]
        Neighbor labels of each cell. A cell is never its own neighbor and
        no neighbor is listed twice, even on grids narrower than 3 cells.

    Raises
    ------
    ValueError
        If ``strategy`` is unknown.

    Examples
    --------
    >>> n = grid_neighbors(["0-0", "0-1", "0-2", "1-0", "1-1", "1-2",
    ...                     "2-0", "2-1", "2-2"], wrap=True)
    >>> sorted(n["0-0"])
    ['0-1', '0-2', '1-0', '2-0']
    """
    try:
        offsets = _STRATEGIES[strategy]
    except KeyError:
        raise ValueError(
            f"strategy must be one of {sorted(_STRATEGIES)}, got {strategy!r}."
        ) from None

    labels = list(index)
    positions = {label: parse_idx(label) for label in labels}
    n_rows = max(p.row for p in positions.values()) + 1
    n_cols = max(p.col for p in positions.values()) + 1

    neighbors: dict[str, list[str]] = {}
    for label, (row, col) in positions.items():
        found: list[str] = []
        for d_row, d_col in offsets:
            r, c = row + d_row, col + d_col
            if wrap:
                r, c = r % n_rows, c % n_cols
            elif not (0 <= r < n_rows and 0 <= c < n_cols):
                continue
            neighbor = f"{r}-{c}"
            if neighbor != label and neighbor not in found and neighbor in positions:
                found.append(neighbor)
        neighbors[label] = found
    return neighbors


__all__ = ["MOORE", "VON_NEUMANN", "grid_neighbors"]
