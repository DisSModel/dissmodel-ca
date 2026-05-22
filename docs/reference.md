# DisSModel-CA Model Reference

This section provides a detailed reference for the Cellular Automata (CA) models available in `dissmodel-ca`. These models follow the spatial modeling conventions established by the TerraME package, mapping ecological and physical theories into efficient spatial implementations.

---

### Anneal (Majority-Vote Smoothing)

**1. Description:**
The Anneal model is a majority-vote variant of cellular automata that produces smooth, blob-like regions. It is often used to simulate physical processes like annealing in metallurgy.

**2. States:**
- `0` - Left (L): Represented as state `0`.
- `1` - Right (R): Represented as state `1`.

**3. Neighborhood:**
This model utilizes a **Moore (Queen) neighborhood** (8 neighbors + self).

**4. Transition Rules:**
The next state of a cell is determined by the total count of cells in state `L` within its neighborhood (including itself):
- If the count is **3 or less**, the cell becomes state **R**.
- If the count is **exactly 4**, the cell becomes state **L**.
- If the count is **exactly 5**, the cell becomes state **R**.
- If the count is **6 or more**, the cell becomes state **L**.

```python
def rule(self, idx: Any) -> int:
    state = self.gdf.loc[idx, self.state_attr]
    # Count neighbors in state L, including the cell itself
    count = (self.neighbor_values(idx, self.state_attr) == AnnealState.L).sum()
    if state == AnnealState.L:
        count += 1

    if count <= 3: return AnnealState.R
    if count == 4: return AnnealState.L
    if count == 5: return AnnealState.R
    return AnnealState.L  # count >= 6
```

**5. Usage Example:**
```python
from dissmodel_ca.models import Anneal
ca = Anneal(gdf=grid)
ca.initialize()
env.run()
```

---

### Excitable Medium

**1. Description:**
Characterizes systems that respond to stimuli by creating a wave of activity that propagates through space, followed by a refractory period.

**2. States:**
- `0` - Resting
- `1` - Excited
- `2, 3, 4, 5` - Refractory

**3. Neighborhood:**
**Von Neumann (Rook)** neighborhood (4 neighbors).

**4. Transition Rules:**
- **Resting state (0):** Becomes **Excited (1)** if at least one neighbor is active (> 0).
- **Other states (1–5):** Advance automatically by 1 modulo 6.

```python
def rule(self, idx: Any) -> int:
    state = self.gdf.loc[idx, self.state_attr]

    if state == 0:
        if (self.neighbor_values(idx, self.state_attr) > 0).any():
            return 1
        return 0

    # Refractory cycle: 1→2→3→4→5→0
    return (state + 1) % 6
```

**5. Usage Example:**
```python
from dissmodel_ca.models import Excitable
exc = Excitable(gdf=grid, dim=50)
exc.initialize()
env.run()
```

---

### Forest Fire (Vector)

**1. Description:**
Simulates the spread of a forest fire across a landscape.

**2. States:**
- `0` - Forest
- `1` - Burning
- `2` - Burned

**3. Neighborhood:**
**Von Neumann (Rook)** neighborhood (4 neighbors).

**4. Transition Rules:**
- **Burning → Burned**
- **Forest → Burning** if any neighbor is burning.

```python
def rule(self, idx: Any) -> int:
    state = self.gdf.loc[idx, self.state_attr]

    if state == FireState.BURNING:
        return FireState.BURNED

    if state == FireState.FOREST:
        if (self.neighbor_values(idx, self.state_attr) == FireState.BURNING).any():
            return FireState.BURNING

    return state
```

**5. Usage Example:**
```python
from dissmodel_ca.models import FireModel
fire = FireModel(gdf=grid)
fire.setup(initial_fire_density=0.05)
fire.initialize()
```

---

### Probabilistic Forest Fire

**1. Description:**
Adds spontaneous combustion and forest regrowth to the fire simulation.

**2. States:**
`0 - Forest`, `1 - Burning`, `2 - Burned`.

**3. Neighborhood:**
**Moore (Queen)** neighborhood (8 neighbors).

**4. Transition Rules:**
- **Forest → Burning** if a neighbor is burning OR by spontaneous combustion.
- **Burned → Forest** by regrowth.

```python
def rule(self, idx: Any) -> int:
    state = self.gdf.loc[idx, self.state_attr]

    if state == FireState.FOREST:
        if (self.neighbor_values(idx, self.state_attr) == FireState.BURNING).any():
            return FireState.BURNING
        return FireState.BURNING if random.random() <= self.prob_combustion else FireState.FOREST

    if state == FireState.BURNING:
        return FireState.BURNED

    # BURNED recovery
    return FireState.FOREST if random.random() <= self.prob_regrowth else FireState.BURNED
```

**5. Usage Example:**
```python
from dissmodel_ca.models import FireModelProb
fire = FireModelProb(gdf=grid)
fire.setup(prob_combustion=0.001, prob_regrowth=0.05)
```

---

### Forest Fire (Raster)

**1. Description:**
NumPy-optimized vectorized version of the Forest Fire model.

**2. States:**
`0 - Forest`, `1 - Burning`, `2 - Burned`.

**3. Neighborhood:**
**Von Neumann (Rook)**.

**4. Transition Rules:**
Vectorized implementation of the fire spread logic.

```python
def rule(self, arrays: dict) -> dict:
    state = arrays[self.state_attr]
    has_burning = self.backend.focal_sum_mask(state == int(FireState.BURNING)) > 0

    new_state = state.copy()
    new_state = np.where(state == int(FireState.BURNING), int(FireState.BURNED),  new_state)
    new_state = np.where((state == int(FireState.FOREST)) & has_burning, int(FireState.BURNING), new_state)

    return {self.state_attr: new_state.astype(np.int8)}
```

**5. Usage Example:**
```python
from dissmodel_ca.models import FireModel
fire = FireModel(backend=backend)
fire.initialize()
```

---

### Conway's Game of Life (Vector)

**1. Description:**
The classic zero-player game demonstrating mathematical emergence.

**2. States:**
`0 - Dead`, `1 - Alive`.

**3. Neighborhood:**
**Moore (Queen)** neighborhood (8 neighbors).

**4. Transition Rules:**
- **Survival:** 2 or 3 neighbors.
- **Birth:** Exactly 3 neighbors.

```python
def rule(self, idx: Any) -> int:
    state = self.gdf.loc[idx, self.state_attr]
    live_neighbors = (self.neighbor_values(idx, self.state_attr)).sum()

    if state == 1:
        return 1 if 2 <= live_neighbors <= 3 else 0
    return 1 if live_neighbors == 3 else 0
```

**5. Usage Example:**
```python
from dissmodel_ca.models import GameOfLife
gol = GameOfLife(gdf=grid)
gol.initialize()
```

---

### Conway's Game of Life (Raster)

**1. Description:**
Raster-based implementation of Conway's Game of Life using NumPy.

**2. States:**
`0 - Dead`, `1 - Alive`.

**3. Neighborhood:**
**Moore (Queen)** neighborhood.

**4. Transition Rules:**
Fully vectorized Conway logic.

```python
def rule(self, arrays: dict) -> dict:
    state     = arrays[self.state_attr]
    neighbors = self.backend.focal_sum_mask(state == 1)

    survive   = (state == 1) & np.isin(neighbors, [2, 3])
    born      = (state == 0) & (neighbors == 3)

    return {self.state_attr: np.where(survive | born, 1, 0).astype(np.int8)}
```

**5. Usage Example:**
```python
from dissmodel_ca.models import GameOfLife
gol = GameOfLife(backend=backend)
```

---

### Stochastic Growth

**1. Description:**
Simulates spatial growth from a central seed with a colonization probability.

**2. States:**
`0 - Empty`, `1 - Alive`.

**3. Neighborhood:**
**Moore (Queen)** neighborhood (8 neighbors).

**4. Transition Rules:**
- **ALIVE** stays **ALIVE**.
- **EMPTY** becomes **ALIVE** with probability `probability` if it has neighbors.

```python
def rule(self, idx: Any) -> int:
    state = self.gdf.loc[idx, self.state_attr]

    if state == GrowthState.ALIVE:
        return GrowthState.ALIVE

    alive_neighbors = (self.neighbor_values(idx, self.state_attr) == GrowthState.ALIVE).sum()
    if alive_neighbors > 0 and random.random() < self.probability:
        return GrowthState.ALIVE

    return GrowthState.EMPTY
```

**5. Usage Example:**
```python
from dissmodel_ca.models import Growth
growth = Growth(gdf=grid, dim=40)
growth.initialize()
```

---

### Interspecific Competition

**1. Description:**
Silvertown et al. (1992) model for spatial competition among five grass species.

**2. States:**
`0 to 4` representing Lolium, Agrostis, Holcus, Poa, and Cynosurus.

**3. Neighborhood:**
**Von Neumann (Rook)** neighborhood.

**4. Transition Rules:**
Weighted random sample based on neighboring species density and experimental invasion rates.

```python
def rule(self, idx: Any) -> int:
    current = Species(int(self.gdf.loc[idx, self.state_attr]))
    neighbor_vals = self.neighbor_values(idx, self.state_attr)
    total_neighbors = len(neighbor_vals)

    # Count neighbors by species and calculate weighted invasion probability
    probs: dict[Species, float] = {}
    total_invasion = 0.0
    for val in neighbor_vals:
        s = Species(int(val))
        p = (1 / total_neighbors) * _PROBS[s][current]
        probs[s] = probs.get(s, 0.0) + p
        total_invasion += p

    # Self-retention
    probs[current] = probs.get(current, 0.0) + (1.0 - total_invasion)

    # Weighted random sample
    r = self._rng.random()
    cumsum = 0.0
    for species, p in probs.items():
        cumsum += p
        if r <= cumsum: return int(species)
    return int(current)
```

**5. Usage Example:**
```python
from dissmodel_ca.models import InterspecificCompetition
ic = InterspecificCompetition(gdf=grid, displacement="ModelA")
ic.initialize()
```

---

### Oscillator

**1. Description:**
Emergence of synchronized oscillating domains from local modulated counters.

**2. States:**
16 integer states (0 to 15).

**3. Neighborhood:**
**Moore (Queen)** neighborhood.

**4. Transition Rules:**
Speed modulation based on the presence of state 0 in the neighborhood.

```python
def rule(self, idx: Any) -> int:
    state = int(self.gdf.loc[idx, self.state_attr])
    neighbors = self.neighbor_values(idx, self.state_attr)

    if (neighbors == 0).any():
        return (state + _AMOUNT[state] + 1) % 16
    return (state + 1) % 16
```

**5. Usage Example:**
```python
from dissmodel_ca.models import Oscillator
osc = Oscillator(gdf=grid)
osc.initialize()
```

---

### Host-Parasite Dynamics

**1. Description:**
Spatiotemporal host-parasite wave interactions based on Hassell et al. (1991).

**2. States:**
9 states (0–8) covering host susceptibility, infection, and parasite cycles.

**3. Neighborhood:**
**Von Neumann (Rook)** neighborhood.

**4. Transition Rules:**
Infection of hosts by neighbors and parasitism of latent hosts by neighbors.

```python
def rule(self, idx: Any) -> int:
    state = self.gdf.loc[idx, self.state_attr]
    neighbors = self.neighbor_values(idx, self.state_attr)

    if state == 0: return 1 if (neighbors == 1).any() else 0
    if state == 1: return 2
    if state == 2: return 3
    if state == 3: return 4 if (neighbors == 5).any() else 3
    if state == 4: return 5
    if state == 5: return 6
    if state == 6: return 7
    if state == 7: return 8
    return 0
```

**5. Usage Example:**
```python
from dissmodel_ca.models import Parasit
parasit = Parasit(gdf=grid)
parasit.initialize()
```

---

### Parity Rule

**1. Description:**
Expanding symmetric patterns based on the Gilbert parity logic (XOR).

**2. States:**
`0 - OFF`, `1 - ON`.

**3. Neighborhood:**
**Von Neumann (Rook)** neighborhood.

**4. Transition Rules:**
Turns ON if neighbor count is 1 or 3.

```python
def rule(self, idx: Any) -> int:
    count = (self.neighbor_values(idx, self.state_attr) == ParityState.ON).sum()
    return ParityState.ON if count in (1, 3) else ParityState.OFF
```

**5. Usage Example:**
```python
from dissmodel_ca.models import Parity
parity = Parity(gdf=grid, dim=50)
parity.initialize()
```

---

### Stochastic Propagation

**1. Description:**
Permanent spread of a phenomenon with Euclidean k=4 neighbors.

**2. States:**
`0 - OFF`, `1 - ON`.

**3. Neighborhood:**
**K-Nearest Neighbors (KNN)** with k=4.

**4. Transition Rules:**
Permanent activation with probability `prob` if an active neighbor exists.

```python
def rule(self, idx: Any) -> int:
    state = self.gdf.loc[idx, self.state_attr]
    if state == PropagationState.ON: return PropagationState.ON

    has_active_neighbor = (self.neighbor_values(idx, self.state_attr) == PropagationState.ON).any()
    if has_active_neighbor and np.random.rand() < self.prob:
        return PropagationState.ON
    return PropagationState.OFF
```

**5. Usage Example:**
```python
from dissmodel_ca.models import Propagation
prop = Propagation(gdf=grid)
prop.setup(prob=0.15, initial_density=0.10)
```

---

### Snowfall and Accumulation

**1. Description:**
Simulates snowflakes falling and accumulating on the ground or on other flakes.

**2. States:**
`0 - Empty`, `1 - Snow`.

**3. Neighborhood:**
Direct grid index indexing (above/below).

**4. Transition Rules:**
Downward movement, arrival from above, and ground/obstacle accumulation.

```python
def rule(self, idx: Any) -> int:
    cell = self.gdf.loc[idx]
    x, y = parse_idx(idx)
    t = self.env.now()

    # Top row generation
    if y == self.dim - 1:
        if cell.state == SnowState.EMPTY and t < (self.end_time - self.dim) and random.random() < self.probability:
            return SnowState.SNOW
        return SnowState.EMPTY

    # Movement logic (checking below)
    if cell.state == SnowState.SNOW:
        if y == 0: return SnowState.SNOW
        below_state = self.gdf.loc[f"{y-1}-{x}", "state"]
        return SnowState.EMPTY if below_state == SnowState.EMPTY else SnowState.SNOW

    # Arrival logic (checking above)
    above_idx = f"{y + 1}-{x}" if y + 1 < self.dim else None
    if above_idx and self.gdf.loc[above_idx, "state"] == SnowState.SNOW:
        return SnowState.SNOW
    return SnowState.EMPTY
```

**5. Usage Example:**
```python
from dissmodel_ca.models import Snow
snow = Snow(gdf=grid, dim=20)
```

---

### Solid Diffusion

**1. Description:**
Simulates atomic diffusion via random vacancy swapping.

**2. States:**
`0 - Atom1`, `1 - Atom2`, `2 - Vacancy`.

**3. Neighborhood:**
**Moore (Queen)**.

**4. Transition Rules:**
Uses a **sequential random sweep** (updates are handled in `execute()` to ensure atom conservation).

```python
# SolidDiffusion uses execute() for sequential swaps:
def execute(self) -> None:
    indices = list(self.gdf.index)
    self._rng.shuffle(indices)
    for idx in indices:
        if self.gdf.loc[idx, "state"] != int(SolidDiffusionState.VACANCY): continue
        neighbor_ids = _queen_neighbors(idx, self.dim)
        non_vacant = [n for n in neighbor_ids if self.gdf.loc[n, "state"] != int(SolidDiffusionState.VACANCY)]
        if not non_vacant: continue
        chosen = self._rng.choice(non_vacant)
        self.gdf.loc[idx, "state"] = self.gdf.loc[chosen, "state"]
        self.gdf.loc[chosen, "state"] = int(SolidDiffusionState.VACANCY)
```

**5. Usage Example:**
```python
from dissmodel_ca.models import SolidDiffusion
sd = SolidDiffusion(gdf=grid, dim=31)
sd.initialize()
```

---

### Wolfram Elementary CA

**1. Description:**
History of 1D rules visualized row-by-row in 2D.

**2. States:**
`0 - OFF`, `1 - ON`.

**3. Neighborhood:**
1D horizontal (3 cells in the row above).

**4. Transition Rules:**
Lookup in a rule table (0–255).

```python
# Wolfram uses execute() for row-by-row progression:
def execute(self) -> None:
    t = int(self.env.now())
    if t == 0 or t > self.final_time: return
    yc, yn = t - 1, t
    for x in range(self.xdim):
        left, right = (x - 1) % self.xdim, (x + 1) % self.xdim
        conf = f"{int(self.gdf.loc[f'{yc}-{left}', 'state'])}{int(self.gdf.loc[f'{yc}-{x}', 'state'])}{int(self.gdf.loc[f'{yc}-{right}', 'state'])}"
        self.gdf.loc[f"{yn}-{x}", self.state_attr] = self._rule_table[conf]
```

**5. Usage Example:**
```python
from dissmodel_ca.models import Wolfram
wolfram = Wolfram(gdf=grid, final_time=55)
wolfram.initialize()
```
