from __future__ import annotations

import random
from enum import IntEnum
from typing import Any

from libpysal.weights import Rook

from dissmodel.geo import CellularAutomaton, parse_idx


class Species(IntEnum):
    """
    Grass species in :class:`InterspecificCompetition`.

    Attributes
    ----------
    LOLIUM : int
        *Lolium perenne* (0).
    AGROSTIS : int
        *Agrostis stolonifera* (1).
    HOLCUS : int
        *Holcus lanatus* (2).
    POA : int
        *Poa trivialis* (3).
    CYNOSURUS : int
        *Cynosurus cristatus* (4).
    """
    LOLIUM    = 0
    AGROSTIS  = 1
    HOLCUS    = 2
    POA       = 3
    CYNOSURUS = 4


# Empirically determined invasion probabilities from Silvertown et al. (1992).
# _PROBS[invader][defender] = probability that ``invader`` colonises a cell
# currently occupied by ``defender`` per unit time, given one invading neighbor.
_PROBS: dict[Species, dict[Species, float]] = {
    Species.LOLIUM: {
        Species.LOLIUM: 0.00, Species.AGROSTIS: 0.02, Species.HOLCUS: 0.06,
        Species.POA:    0.05, Species.CYNOSURUS: 0.03,
    },
    Species.AGROSTIS: {
        Species.LOLIUM: 0.23, Species.AGROSTIS: 0.00, Species.HOLCUS: 0.09,
        Species.POA:    0.32, Species.CYNOSURUS: 0.37,
    },
    Species.HOLCUS: {
        Species.LOLIUM: 0.06, Species.AGROSTIS: 0.08, Species.HOLCUS: 0.00,
        Species.POA:    0.16, Species.CYNOSURUS: 0.09,
    },
    Species.POA: {
        Species.LOLIUM: 0.44, Species.AGROSTIS: 0.06, Species.HOLCUS: 0.06,
        Species.POA:    0.00, Species.CYNOSURUS: 0.11,
    },
    Species.CYNOSURUS: {
        Species.LOLIUM: 0.03, Species.AGROSTIS: 0.02, Species.HOLCUS: 0.03,
        Species.POA:    0.05, Species.CYNOSURUS: 0.00,
    },
}

# Band thresholds (y <= threshold → assigned species for that band).
# Matches TerraME initial_location = {7, 15, 23, 31, 39} on a 40x40 grid.
_BAND_THRESHOLDS: list[int] = [7, 15, 23, 31, 39]

# Initial species order per model variant (5 horizontal bands, bottom → top).
_INITIAL_BANDS: dict[str, list[Species]] = {
    "ModelA": [Species.AGROSTIS, Species.HOLCUS,    Species.LOLIUM,    Species.CYNOSURUS, Species.POA],
    "ModelB": [Species.AGROSTIS, Species.LOLIUM,    Species.CYNOSURUS, Species.HOLCUS,    Species.POA],
    "ModelC": [Species.AGROSTIS, Species.HOLCUS,    Species.POA,       Species.CYNOSURUS, Species.LOLIUM],
}


class InterspecificCompetition(CellularAutomaton):
    """
    Cellular automaton modelling spatial interspecific competition
    among five grass species.

    At each step, a cell's species can be replaced by a neighbouring
    species with a probability proportional to (i) the fraction of
    neighbors belonging to that species and (ii) its experimentally
    determined invasion rate against the current occupant.

    Includes three initial spatial arrangements (A, B, C) matching the
    model variants from Silvertown et al. (1992), plus a random layout.

    Based on: Silvertown J., Holtier S., Johnson J. & Dale P. (1992).
    *Cellular Automaton Models of Interspecific Competition for Space —
    The Effect of Pattern on Process.*
    Journal of Ecology, 80(3), 527–533.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame with geometries and a ``state`` attribute.
        Should be created with ``dimension=(40, 40)`` to match the
        original model's band proportions.
    **kwargs :
        Extra keyword arguments forwarded to
        :class:`~dissmodel.geo.CellularAutomaton`.

    Examples
    --------
    >>> from dissmodel.geo import vector_grid
    >>> from dissmodel.core import Environment
    >>> gdf = vector_grid(dimension=(40, 40), resolution=1, attrs={"state": 0})
    >>> env = Environment(end_time=200)
    >>> ic = InterspecificCompetition(gdf=gdf, displacement="ModelA")
    >>> ic.initialize()
    """

    def setup(
        self,
        displacement: str = "ModelA",
        seed: int = 42,
    ) -> None:
        """
        Configure the model and build the Von Neumann neighborhood.

        Parameters
        ----------
        displacement : str, optional
            Initial spatial arrangement of species. One of ``"ModelA"``,
            ``"ModelB"``, ``"ModelC"`` (horizontal bands), or
            ``"Random"`` (uniformly shuffled). Default is ``"ModelA"``.
        seed : int, optional
            Random seed, by default 42.

        Raises
        ------
        ValueError
            If ``displacement`` is not one of the accepted values.
        """
        valid = {"ModelA", "ModelB", "ModelC", "Random"}
        if displacement not in valid:
            raise ValueError(f"displacement must be one of {valid}, got '{displacement}'.")
        self.displacement = displacement
        self._rng = random.Random(seed)
        self.create_neighborhood(strategy=Rook, use_index=True)

    def initialize(self) -> None:
        """
        Assign initial species to all cells.

        - ``"ModelA"`` / ``"ModelB"`` / ``"ModelC"``: five horizontal bands
          ordered from bottom (y=0) to top (y=39) according to the
          variant's species sequence and the thresholds
          y <= {7, 15, 23, 31, 39}.
        - ``"Random"``: each cell receives a uniformly random species.
        """
        if self.displacement == "Random":
            all_species = list(Species)
            self.gdf["state"] = [
                int(self._rng.choice(all_species)) for _ in range(len(self.gdf))
            ]
            return

        # Reverse band order: TerraME y=0 is at the bottom (increasing upward),
        # DisSModel renders y=0 at the top — inverting the list corrects the flip.
        band = list(reversed(_INITIAL_BANDS[self.displacement]))

        def assign(idx: str) -> int:
            x, _ = parse_idx(idx)
            for i, threshold in enumerate(_BAND_THRESHOLDS):
                if x <= threshold:
                    return int(band[i])
            return int(band[-1])

        self.gdf["state"] = self.gdf.index.map(assign)

    def rule(self, idx: Any) -> int:
        """
        Apply the species invasion rule to cell ``idx``.

        Builds a probability distribution over all species present in the
        neighborhood weighted by invasion rates, adds self-retention to
        make probabilities sum to 1, then samples the outcome.

        Parameters
        ----------
        idx : any
            Index of the cell being evaluated.

        Returns
        -------
        int
            The species occupying the cell after this step.
        """
        current = Species(int(self.gdf.loc[idx, self.state_attr]))
        neighbor_vals = self.neighbor_values(idx, self.state_attr)
        total_neighbors = len(neighbor_vals)

        # Count neighbors by species
        count_by_species: dict[Species, int] = {}
        for val in neighbor_vals:
            s = Species(int(val))
            count_by_species[s] = count_by_species.get(s, 0) + 1

        # Invasion probabilities for each species present in the neighborhood
        probs: dict[Species, float] = {}
        total_invasion = 0.0
        for species, count in count_by_species.items():
            p = (count / total_neighbors) * _PROBS[species][current]
            probs[species] = probs.get(species, 0.0) + p
            total_invasion += p

        # Self-retention: probability the current species holds its cell
        probs[current] = probs.get(current, 0.0) + (1.0 - total_invasion)

        # Weighted random sample
        r = self._rng.random()
        cumsum = 0.0
        for species, p in probs.items():
            cumsum += p
            if r <= cumsum:
                return int(species)

        return int(current)  # floating-point safety fallback


__all__ = ["InterspecificCompetition", "Species"]