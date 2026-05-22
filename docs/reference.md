# DisSModel-CA Model Reference

This section provides a detailed reference for the Cellular Automata (CA) models available in `dissmodel-ca`. These models follow the spatial modeling conventions established by the TerraME package, mapping ecological and physical theories into efficient spatial implementations.

---

### Anneal (Majority-Vote Smoothing)

**1. Description:**
The Anneal model is a majority-vote variant of cellular automata that produces smooth, blob-like regions. It is often used to simulate physical processes like annealing in metallurgy.

**2. States:**
- `0` - Left (L)
- `1` - Right (R)

**3. Neighborhood:**
**Moore (Queen)** neighborhood (8 neighbors + self).

**4. Transition Rules:**
The next state of a cell is determined by the total count of cells in state `L` within its neighborhood (including itself):
- If the count is **3 or less**, the cell becomes state **R**.
- If the count is **exactly 4**, the cell becomes state **L**.
- If the count is **exactly 5**, the cell becomes state **R**.
- If the count is **6 or more**, the cell becomes state **L**.

```python
def rule(self, idx: Any) -> int:
    state = self.gdf.loc[idx, self.state_attr]
    count = (self.neighbor_values(idx, self.state_attr) == AnnealState.L).sum()
    if state == AnnealState.L:
        count += 1

    if count <= 3: return AnnealState.R
    if count == 4: return AnnealState.L
    if count == 5: return AnnealState.R
    return AnnealState.L
```

**5. Usage Example:**
```python
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel_ca.models import Anneal

# 1. Create Space
grid = vector_grid(dimension=(20, 20), resolution=1, attrs={"state": 0})

# 2. Setup Environment
env = Environment(end_time=10)

# 3. Instantiate and Run Model
ca = Anneal(gdf=grid)
ca.initialize()  # Random distribution of L and R
env.run()
```

---

### Excitable Medium

**1. Description:**
Systems that respond to stimuli by creating a wave of activity that propagates through space, followed by a refractory period.

**2. States:**
- `0` - Resting
- `1` - Excited
- `2, 3, 4, 5` - Refractory

**3. Neighborhood:**
**Von Neumann (Rook)** neighborhood (4 neighbors).

**4. Transition Rules:**
```python
def rule(self, idx: Any) -> int:
    state = self.gdf.loc[idx, self.state_attr]
    if state == 0:
        if (self.neighbor_values(idx, self.state_attr) > 0).any():
            return 1
        return 0
    return (state + 1) % 6
```

**5. Usage Example:**
```python
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel_ca.models import Excitable

grid = vector_grid(dimension=(50, 50), resolution=1, attrs={"state": 0})
env = Environment(end_time=500)

exc = Excitable(gdf=grid, dim=50)
exc.initialize() # Places seeds for spiral waves
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
```python
def rule(self, idx: Any) -> int:
    state = self.gdf.loc[idx, self.state_attr]
    if state == FireState.BURNING: return FireState.BURNED
    if state == FireState.FOREST:
        if (self.neighbor_values(idx, self.state_attr) == FireState.BURNING).any():
            return FireState.BURNING
    return state
```

**5. Usage Example:**
```python
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel_ca.models import FireModel

grid = vector_grid(dimension=(20, 20), resolution=1, attrs={"state": 0})
env = Environment(end_time=20)

fire = FireModel(gdf=grid)
fire.setup(initial_fire_density=0.05)
fire.initialize()
env.run()
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
```python
def rule(self, idx: Any) -> int:
    state = self.gdf.loc[idx, self.state_attr]
    if state == FireState.FOREST:
        if (self.neighbor_values(idx, self.state_attr) == FireState.BURNING).any():
            return FireState.BURNING
        return FireState.BURNING if random.random() <= self.prob_combustion else FireState.FOREST
    if state == FireState.BURNING: return FireState.BURNED
    return FireState.FOREST if random.random() <= self.prob_regrowth else FireState.BURNED
```

**5. Usage Example:**
```python
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel_ca.models import FireModelProb

grid = vector_grid(dimension=(20, 20), resolution=1, attrs={"state": 0})
env = Environment(end_time=100)

fire = FireModelProb(gdf=grid)
fire.setup(prob_combustion=0.001, prob_regrowth=0.05)
env.run()
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
from dissmodel.core import Environment
from dissmodel.geo.raster.backend import RasterBackend
from dissmodel_ca.models import FireModel

backend = RasterBackend(shape=(100, 100))
env = Environment(start_time=1, end_time=50)

fire = FireModel(backend=backend)
fire.setup(backend=backend, initial_fire_density=0.02)
fire.initialize()
env.run()
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
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel_ca.models import GameOfLife

grid = vector_grid(dimension=(30, 30), resolution=1, attrs={"state": 0})
env = Environment(end_time=50)

gol = GameOfLife(gdf=grid)
gol.initialize() # Random distribution
env.run()
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
from dissmodel.core import Environment
from dissmodel.geo.raster_grid import raster_grid
from dissmodel_ca.models import GameOfLife

backend = raster_grid(100, 100, attrs={"state": 0})
env = Environment(start_time=1, end_time=100)

gol = GameOfLife(backend=backend)
gol.initialize()
env.run()
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
```python
def rule(self, idx: Any) -> int:
    state = self.gdf.loc[idx, self.state_attr]
    if state == GrowthState.ALIVE: return GrowthState.ALIVE
    alive_neighbors = (self.neighbor_values(idx, self.state_attr) == GrowthState.ALIVE).sum()
    if alive_neighbors > 0 and random.random() < self.probability:
        return GrowthState.ALIVE
    return GrowthState.EMPTY
```

**5. Usage Example:**
```python
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel_ca.models import Growth

grid = vector_grid(dimension=(40, 40), resolution=1, attrs={"state": 0})
env = Environment(end_time=50)

growth = Growth(gdf=grid, dim=40)
growth.setup(probability=0.20)
growth.initialize() # Central seed
env.run()
```

---

### Interspecific Competition

**1. Description:**
Silvertown et al. (1992) model for spatial competition among five grass species.

**2. States:**
`0 to 4` (Lolium, Agrostis, Holcus, Poa, Cynosurus).

**3. Neighborhood:**
**Von Neumann (Rook)** neighborhood.

**4. Transition Rules:**
```python
def rule(self, idx: Any) -> int:
    current = Species(int(self.gdf.loc[idx, self.state_attr]))
    neighbor_vals = self.neighbor_values(idx, self.state_attr)
    total_neighbors = len(neighbor_vals)
    probs: dict[Species, float] = {}
    total_invasion = 0.0
    for val in neighbor_vals:
        s = Species(int(val))
        p = (1 / total_neighbors) * _PROBS[s][current]
        probs[s] = probs.get(s, 0.0) + p
        total_invasion += p
    probs[current] = probs.get(current, 0.0) + (1.0 - total_invasion)
    # ... weighted random sample ...
```

**5. Usage Example:**
```python
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel_ca.models import InterspecificCompetition

grid = vector_grid(dimension=(40, 40), resolution=1, attrs={"state": 0})
env = Environment(end_time=500)

ic = InterspecificCompetition(gdf=grid, displacement="ModelA")
ic.initialize() # Species bands
env.run()
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
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel_ca.models import Oscillator

grid = vector_grid(dimension=(50, 50), resolution=1, attrs={"state": 0})
env = Environment(end_time=400)

osc = Oscillator(gdf=grid)
osc.initialize()
env.run()
```

---

### Host-Parasite Dynamics

**1. Description:**
Spatiotemporal host-parasite wave interactions based on Hassell et al. (1991).

**2. States:**
9 states (0–8).

**3. Neighborhood:**
**Von Neumann (Rook)** neighborhood.

**4. Transition Rules:**
```python
def rule(self, idx: Any) -> int:
    state = self.gdf.loc[idx, self.state_attr]
    neighbors = self.neighbor_values(idx, self.state_attr)
    if state == 0: return 1 if (neighbors == 1).any() else 0
    if state == 3: return 4 if (neighbors == 5).any() else 3
    # ... automatic progression for other states ...
```

**5. Usage Example:**
```python
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel_ca.models import Parasit

grid = vector_grid(dimension=(50, 50), resolution=1, attrs={"state": 0})
env = Environment(end_time=500)

parasit = Parasit(gdf=grid)
parasit.initialize()
env.run()
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
```python
def rule(self, idx: Any) -> int:
    count = (self.neighbor_values(idx, self.state_attr) == ParityState.ON).sum()
    return ParityState.ON if count in (1, 3) else ParityState.OFF
```

**5. Usage Example:**
```python
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel_ca.models import Parity

grid = vector_grid(dimension=(50, 50), resolution=1, attrs={"state": 0})
env = Environment(end_time=100)

parity = Parity(gdf=grid, dim=50)
parity.initialize() # Canonical seeds
env.run()
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
```python
def rule(self, idx: Any) -> int:
    state = self.gdf.loc[idx, self.state_attr]
    if state == PropagationState.ON: return PropagationState.ON
    if (self.neighbor_values(idx, self.state_attr) == PropagationState.ON).any() and np.random.rand() < self.prob:
        return PropagationState.ON
    return PropagationState.OFF
```

**5. Usage Example:**
```python
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel_ca.models import Propagation

grid = vector_grid(dimension=(20, 20), resolution=1, attrs={"state": 0})
env = Environment(end_time=20)

prop = Propagation(gdf=grid)
prop.setup(prob=0.15, initial_density=0.10)
prop.initialize()
env.run()
```

---

### Snowfall and Accumulation

**1. Description:**
Simulates snowflakes falling and accumulating.

**2. States:**
`0 - Empty`, `1 - Snow`.

**3. Neighborhood:**
Direct grid index indexing.

**4. Transition Rules:**
```python
def rule(self, idx: Any) -> int:
    # Logic for downward movement and ground accumulation
    # checking y-1 (below) and y+1 (above)
```

**5. Usage Example:**
```python
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel_ca.models import Snow

grid = vector_grid(dimension=(20, 20), resolution=1, attrs={"state": 0})
env = Environment(end_time=60)

snow = Snow(gdf=grid, dim=20)
snow.setup(probability=0.05)
env.run()
```

---

### Solid Diffusion

**1. Description:**
Atomic diffusion via random vacancy swapping.

**2. States:**
`0 - Atom1`, `1 - Atom2`, `2 - Vacancy`.

**3. Neighborhood:**
**Moore (Queen)**.

**4. Transition Rules:**
Uses a **sequential random sweep** in `execute()`.

**5. Usage Example:**
```python
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel_ca.models import SolidDiffusion

grid = vector_grid(dimension=(31, 31), resolution=1, attrs={"state": 0})
env = Environment(end_time=500)

sd = SolidDiffusion(gdf=grid, dim=31)
sd.initialize() # Separates Atom1 and Atom2
env.run()
```

---

### Wolfram Elementary CA

**1. Description:**
History of 1D rules visualized row-by-row in 2D.

**2. States:**
`0 - OFF`, `1 - ON`.

**3. Neighborhood:**
1D horizontal (above row).

**4. Transition Rules:**
Lookup in a rule table (0–255) via `execute()`.

**5. Usage Example:**
```python
from dissmodel.core import Environment
from dissmodel.geo import vector_grid
from dissmodel_ca.models import Wolfram

grid = vector_grid(dimension=(111, 56), resolution=1, attrs={"state": 0})
env = Environment(end_time=55)

wolfram = Wolfram(gdf=grid, final_time=55)
wolfram.setup(rule_number=90, final_time=55)
wolfram.initialize()
env.run()
```
