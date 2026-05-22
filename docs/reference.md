# DisSModel-CA Model Reference

This section provides a detailed reference for the Cellular Automata (CA) models available in `dissmodel-ca`. These models follow the spatial modeling conventions established by the TerraME package, mapping ecological and physical theories into efficient spatial implementations.

---

### Anneal (Majority-Vote Smoothing)

**1. Description:**
The Anneal model is a majority-vote variant of cellular automata that produces smooth, blob-like regions. It is often used to simulate physical processes like annealing in metallurgy, where materials are heated and cooled to remove internal stresses and toughen them. In a spatial context, it acts as a filter that reduces noise and aggregates isolated cells into larger, coherent patches.

**2. States:**
- `0` - Left (L): Represented as state `0`.
- `1` - Right (R): Represented as state `1`.

**3. Neighborhood:**
This model utilizes a **Moore (Queen) neighborhood**, considering the 8 surrounding cells plus the cell itself (9 cells total for the majority count).

**4. Transition Rules:**
The next state of a cell is determined by the total count of cells in state `L` within its neighborhood (including itself):
- If the count is **3 or less**, the cell becomes state **R**.
- If the count is **exactly 4**, the cell becomes state **L**.
- If the count is **exactly 5**, the cell becomes state **R**.
- If the count is **6 or more**, the cell becomes state **L**.

**5. Usage Example:**
```python
from dissmodel.geo import vector_grid
from dissmodel.core import Environment
from dissmodel_ca.models import Anneal

# Create a 20x20 vector grid with an initial state attribute
grid = vector_grid(dimension=(20, 20), resolution=1, attrs={"state": 0})

# Set up the simulation environment
env = Environment(end_time=10)

# Instantiate the Anneal model
ca = Anneal(gdf=grid)

# Initialize with a random distribution of L and R states
ca.initialize()

# Run the simulation
env.run()
```

---

### Excitable Medium

**1. Description:**
This model implements an excitable medium rule, which characterizes systems that can respond to stimuli by creating a wave of activity that propagates through space. Examples include chemical reactions (like the Belousov-Zhabotinsky reaction) or biological tissues (like cardiac muscle). Once excited, a cell enters a refractory period during which it cannot be re-excited, ensuring that waves propagate outwards without immediate back-propagation.

**2. States:**
The model uses 6 discrete states:
- `0` - Resting: The cell is quiescent but susceptible to excitation.
- `1` - Excited: The peak of the activity wave.
- `2, 3, 4, 5` - Refractory: The cell is recovering and cannot be re-excited.

**3. Neighborhood:**
The model uses a **Von Neumann (Rook) neighborhood**, considering only the 4 cardinal neighbors (North, South, East, West).

**4. Transition Rules:**
The transition logic follows a deterministic cycle:
- **Resting state (0):** If at least one neighbor is in an excited or refractory state (state > 0), the cell becomes **Excited (1)**. Otherwise, it remains at state 0.
- **Excited and Refractory states (1–5):** The cell automatically advances to the next state in the sequence (1→2→3→4→5→0) at each time step.

**5. Usage Example:**
```python
from dissmodel.geo import vector_grid
from dissmodel.core import Environment
from dissmodel_ca.models import Excitable

# Create a 50x50 grid (canonical size for this model)
grid = vector_grid(dimension=(50, 50), resolution=1, attrs={"state": 0})

# Set up the environment for 500 steps to observe spiral patterns
env = Environment(end_time=500)

# Instantiate the Excitable medium model
# We pass dim=50 to allow the model to locate seed cells
exc = Excitable(gdf=grid, dim=50)

# Initialize with two seed cells to generate spiral waves
exc.initialize()

# Run the simulation
env.run()
```

---

### Forest Fire (Vector)

**1. Description:**
A spatial cellular automaton simulating the spread of a forest fire. The model captures the fundamental dynamics of fire propagation across a landscape, where the presence of fire in a cell triggers the ignition of its susceptible neighbors.

**2. States:**
- `0` - Forest: Healthy trees, susceptible to catching fire.
- `1` - Burning: Actively burning, spreads fire to neighbors.
- `2` - Burned: Consumed by fire, no longer flammable.

**3. Neighborhood:**
The model uses a **Von Neumann (Rook) neighborhood** (4 cardinal neighbors).

**4. Transition Rules:**
- **Burning → Burned:** A cell that is currently burning will always become burned in the next step.
- **Forest → Burning:** A forest cell will catch fire if at least one of its four direct neighbors is currently burning.
- **Otherwise:** The state remains unchanged (Burned cells stay burned, and isolated Forest stays forest).

**5. Usage Example:**
```python
from dissmodel.geo import vector_grid
from dissmodel.core import Environment
from dissmodel_ca.models import FireModel

# Create a 10x10 forest grid
grid = vector_grid(dimension=(10, 10), resolution=1, attrs={"state": 0})

# Set up the simulation environment
env = Environment(end_time=10)

# Instantiate the model with 5% initial fire density
fire = FireModel(gdf=grid)
fire.setup(initial_fire_density=0.05)

# Randomly distribute the initial fire
fire.initialize()

# Run the simulation
env.run()
```

---

### Probabilistic Forest Fire

**1. Description:**
This model extends the basic forest fire simulation by introducing stochastic processes. It includes spontaneous combustion (e.g., lightning strikes) and forest regrowth. These additions allow for long-term coexistence of fire and forest, leading to complex, dynamic spatial patterns rather than a simple one-way consumption of the landscape.

**2. States:**
- `0` - Forest: Susceptible trees.
- `1` - Burning: Actively spreading fire.
- `2` - Burned: Non-flammable, but can regrow.

**3. Neighborhood:**
Unlike the basic model, this version uses a **Moore (Queen) neighborhood** (8 neighbors).

**4. Transition Rules:**
- **Forest → Burning:** Occurs if any neighbor is burning **OR** with a small probability of spontaneous combustion (`prob_combustion`).
- **Burning → Burned:** A burning cell always becomes burned in the next step.
- **Burned → Forest:** A burned cell recovers and becomes forest again with a specific probability (`prob_regrowth`).

**5. Usage Example:**
```python
from dissmodel.geo import vector_grid
from dissmodel.core import Environment
from dissmodel_ca.models import FireModelProb

# Create a grid for a long-term simulation
grid = vector_grid(dimension=(20, 20), resolution=1, attrs={"state": 0})

# Run for 100 steps to see the balance between fire and regrowth
env = Environment(end_time=100)

# Instantiate the probabilistic model
fire = FireModelProb(gdf=grid)

# Set the probabilities for spontaneous combustion and regrowth
fire.setup(prob_combustion=0.001, prob_regrowth=0.05)

# Run the simulation
env.run()
```

---

### Forest Fire (Raster)

**1. Description:**
This is the raster-optimized version of the Forest Fire model. While it follows the exact same logic as the vector `FireModel`, it is implemented using NumPy's vectorized operations for significantly higher performance on large grids.

**2. States:**
- `0` - Forest
- `1` - Burning
- `2` - Burned

**3. Neighborhood:**
**Von Neumann (Rook)** neighborhood (4 directions).

**4. Transition Rules:**
Identical to the vector model, but applied simultaneously to all cells:
- Cells in state `BURNING` transition to `BURNED`.
- Cells in state `FOREST` transition to `BURNING` if the focal sum of `BURNING` neighbors is greater than 0.

**5. Usage Example:**
```python
import numpy as np
from dissmodel.core import Environment
from dissmodel.geo.raster.backend import RasterBackend
from dissmodel_ca.models import FireModel, FireState

# Initialize a 100x100 raster backend
backend = RasterBackend(shape=(100, 100))

# Set up the environment
env = Environment(start_time=1, end_time=50)

# Instantiate the raster model
fire = FireModel(backend=backend)

# Setup with 2% initial fire density
fire.setup(backend=backend, initial_fire_density=0.02)

# Randomly initialize the grid state
fire.initialize()

# Run the simulation
env.run()
```

---

### Conway's Game of Life (Vector)

**1. Description:**
The classic zero-player game devised by John Conway in 1970. It is a Turing-complete cellular automaton that demonstrates how complex patterns and behaviors can emerge from a few simple rules. It is the most famous example of mathematical emergence.

**2. States:**
- `0` - Dead: An empty or inactive cell.
- `1` - Alive: A cell containing an organism.

**3. Neighborhood:**
**Moore (Queen)** neighborhood (8 neighbors).

**4. Transition Rules:**
- **Survival:** A live cell with 2 or 3 live neighbors stays alive.
- **Death:** A live cell with fewer than 2 (underpopulation) or more than 3 (overpopulation) live neighbors dies.
- **Birth:** A dead cell with exactly 3 live neighbors becomes alive (reproduction).

**5. Usage Example:**
```python
from dissmodel.geo import vector_grid
from dissmodel.core import Environment
from dissmodel_ca.models import GameOfLife

# Create a 30x30 grid
grid = vector_grid(dimension=(30, 30), resolution=1, attrs={"state": 0})

# Environment setup
env = Environment(end_time=50)

# Instantiate the model
gol = GameOfLife(gdf=grid)

# You can initialize with a random distribution
gol.initialize()

# Or place specific patterns like gliders or pulsars
# gol.initialize_patterns(patterns=["glider", "pulsar"])

# Run the simulation
env.run()
```

---

### Conway's Game of Life (Raster)

**1. Description:**
The raster-based implementation of Conway's Game of Life. It utilizes vectorized focal sums to calculate the neighbor counts for all cells at once, making it suitable for very large-scale simulations that would be too slow in a vector-based approach.

**2. States:**
- `0` - Dead
- `1` - Alive

**3. Neighborhood:**
**Moore (Queen)** neighborhood (8 directions).

**4. Transition Rules:**
The standard Conway rules implemented via vectorized logic:
- A cell survives if it is alive and has 2 or 3 neighbors.
- A cell is born if it is dead and has exactly 3 neighbors.
- All other cells transition to or remain in the dead state.

**5. Usage Example:**
```python
import numpy as np
from dissmodel.core import Environment
from dissmodel.geo.raster_grid import raster_grid
from dissmodel_ca.models import GameOfLife

# Create a raster grid with a random initial state
rng = np.random.default_rng(42)
grid_data = rng.integers(0, 2, (100, 100))
backend = raster_grid(100, 100, attrs={"state": grid_data})

# Setup environment
env = Environment(start_time=1, end_time=100)

# Instantiate the raster Game of Life
gol = GameOfLife(backend=backend)

# Run the simulation
env.run()
```

---

### Stochastic Growth

**1. Description:**
This model simulates spatial growth from a single central seed. It represents processes like the growth of a bacterial colony, the spread of a city from a historical center, or the diffusion of an innovation. The growth is stochastic, meaning it depends on a colonization probability.

**2. States:**
- `0` - Empty: Uncolonized space.
- `1` - Alive: Colonized space.

**3. Neighborhood:**
**Moore (Queen)** neighborhood (8 neighbors).

**4. Transition Rules:**
- **Persistence:** Once a cell is `ALIVE`, it remains `ALIVE` forever (no death).
- **Colonization:** An `EMPTY` cell becomes `ALIVE` with a probability defined by `probability` if it has **at least one** neighbor that is already `ALIVE`.

**5. Usage Example:**
```python
from dissmodel.geo import vector_grid
from dissmodel.core import Environment
from dissmodel_ca.models import Growth

# Create a 40x40 grid
grid = vector_grid(dimension=(40, 40), resolution=1, attrs={"state": 0})

# Environment setup
env = Environment(end_time=50)

# Instantiate growth model with a 20% colonization probability
# Note: we pass dim=40 to help the model find the center cell
growth = Growth(gdf=grid, dim=40)
growth.setup(probability=0.20)

# Initialize with a single seed in the center
growth.initialize()

# Run the simulation
env.run()
```

---

### Interspecific Competition

**1. Description:**
Based on Silvertown et al. (1992), this model simulates the spatial competition among five grass species. It demonstrates how spatial patterns and local interactions determine the long-term survival and distribution of species, even when one might appear dominant in non-spatial models.

**2. States:**
The model tracks five species:
- `0` - *Lolium perenne* (Lolium)
- `1` - *Agrostis stolonifera* (Agrostis)
- `2` - *Holcus lanatus* (Holcus)
- `3` - *Poa trivialis* (Poa)
- `4` - *Cynosurus cristatus* (Cynosurus)

**3. Neighborhood:**
**Von Neumann (Rook)** neighborhood (4 neighbors).

**4. Transition Rules:**
At each step, a cell's species can be replaced by a neighboring species. The probability of invasion depends on:
- The fraction of neighbors belonging to the invading species.
- The experimentally determined invasion rate of the invader against the current occupant.
- If no invasion occurs, the current occupant retains the cell (self-retention).

!!! info "Theoretical Note"
    This model captures the "rock-paper-scissors" style dynamics where no single species is absolutely dominant, allowing for spatial coexistence through local competition.

**5. Usage Example:**
```python
from dissmodel.geo import vector_grid
from dissmodel.core import Environment
from dissmodel_ca.models import InterspecificCompetition

# Create a 40x40 grid (matching the original research)
grid = vector_grid(dimension=(40, 40), resolution=1, attrs={"state": 0})

# Environment setup
env = Environment(end_time=500)

# Instantiate with a specific initial spatial arrangement ("ModelA")
ic = InterspecificCompetition(gdf=grid, displacement="ModelA")

# Initialize the bands of species
ic.initialize()

# Run the simulation
env.run()
```

---

### Oscillator

**1. Description:**
The Oscillator model demonstrates how synchronized oscillating domains and complex wave-like patterns can emerge from local interactions. Cells act as counters that increment their state, but their speed is modulated by the presence of a "trigger" state (state 0) in their neighborhood.

**2. States:**
Cells cycle through **16 integer states** (0 to 15).

**3. Neighborhood:**
**Moore (Queen)** neighborhood (8 neighbors).

**4. Transition Rules:**
The next state depends on whether any neighbor is currently in state `0`:
- **State 0 neighbor present:** The cell advances according to a non-uniform speed table: `new_state = (state + AMOUNT[state] + 1) % 16`.
- **No State 0 neighbor:** The cell advances by exactly one: `new_state = (state + 1) % 16`.

**5. Usage Example:**
```python
from dissmodel.geo import vector_grid
from dissmodel.core import Environment
from dissmodel_ca.models import Oscillator

# Create a 50x50 grid
grid = vector_grid(dimension=(50, 50), resolution=1, attrs={"state": 0})

# Environment setup
env = Environment(end_time=400)

# Instantiate the Oscillator model
osc = Oscillator(gdf=grid)

# Initialize with a random distribution of states 0-15
osc.initialize()

# Run the simulation
env.run()
```

---

### Host-Parasite Dynamics

**1. Description:**
Based on Hassell et al. (1991), this model simulates the spatiotemporal interaction between an insect host and its parasite. It captures how spatial structure allows for the coexistence of both populations, often producing chaotic or spiral-like waves of infection and recovery.

**2. States:**
Cells cycle through 9 states (0–8):
- `0`: Susceptible host.
- `1–2`: Infected host (actively infectious at state 1).
- `3`: Latent parasite.
- `4–8`: Parasite life cycle (mature and infectious at state 5).

**3. Neighborhood:**
**Von Neumann (Rook)** neighborhood (4 neighbors).

**4. Transition Rules:**
- **Infection (0 → 1):** A susceptible host (0) becomes infected if any neighbor is infectious (state 1).
- **Host Progression (1 → 2 → 3):** Advances automatically each step.
- **Parasitism (3 → 4):** A latent parasite (3) becomes active if any neighbor is a mature parasite (state 5).
- **Parasite Cycle (4 → 5 → 6 → 7 → 8 → 0):** Advances automatically, eventually returning the cell to the susceptible host state.

**5. Usage Example:**
```python
from dissmodel.geo import vector_grid
from dissmodel.core import Environment
from dissmodel_ca.models import Parasit

# Create a 50x50 grid
grid = vector_grid(dimension=(50, 50), resolution=1, attrs={"state": 0})

# Environment setup
env = Environment(end_time=500)

# Instantiate the model
parasit = Parasit(gdf=grid)

# Initialize with a random mix of all life cycle states
parasit.initialize()

# Run the simulation
env.run()
```

---

### Parity Rule

**1. Description:**
The Parity rule (also known as the Gilbert rule) is a simple XOR-like logic applied to a spatial grid. Starting from isolated seeds, it produces perfectly symmetric, expanding diamond-shaped wave patterns. It is often used to study geometric growth and self-replication in cellular automata.

**2. States:**
- `0` - OFF: Inactive cell.
- `1` - ON: Active cell.

**3. Neighborhood:**
**Von Neumann (Rook)** neighborhood (4 neighbors).

**4. Transition Rules:**
A cell's state in the next step depends on the count of its `ON` neighbors:
- The cell turns **ON** if it has exactly **1 or 3** neighbors that are `ON`.
- The cell turns **OFF** (or remains OFF) otherwise.

**5. Usage Example:**
```python
from dissmodel.geo import vector_grid
from dissmodel.core import Environment
from dissmodel_ca.models import Parity

# Create a 50x50 grid
grid = vector_grid(dimension=(50, 50), resolution=1, attrs={"state": 0})

# Environment setup
env = Environment(end_time=100)

# Instantiate the model (dim=50 for seed placement)
parity = Parity(gdf=grid, dim=50)

# Place two ON seeds at canonical positions
parity.initialize()

# Run the simulation
env.run()
```

---

### Stochastic Propagation

**1. Description:**
This model simulates the permanent spread of a phenomenon through a population or landscape. Examples include the adoption of a new technology, the spread of an irreversible disease, or the colonization of a new habitat. Once a cell is activated, it never reverts to its original state.

**2. States:**
- `0` - OFF: Inactive cell.
- `1` - ON: Active cell.

**3. Neighborhood:**
This model uses a **K-Nearest Neighbors (KNN)** strategy with **k=4**, meaning each cell interacts with its 4 closest neighbors based on Euclidean distance.

**4. Transition Rules:**
- **Persistence:** Once a cell is `ON`, it stays `ON`.
- **Stochastic Spread:** An `OFF` cell becomes `ON` with a probability `prob` if **at least one** of its 4 nearest neighbors is already `ON`.

**5. Usage Example:**
```python
from dissmodel.geo import vector_grid
from dissmodel.core import Environment
from dissmodel_ca.models import Propagation

# Create a grid
grid = vector_grid(dimension=(20, 20), resolution=1, attrs={"state": 0})

# Environment setup
env = Environment(end_time=20)

# Instantiate the model
prop = Propagation(gdf=grid)

# Configure probabilities and initial density
prop.setup(prob=0.15, initial_density=0.10)

# Initialize the random seeds
prop.initialize()

# Run the simulation
env.run()
```

---

### Snowfall and Accumulation

**1. Description:**
This model simulates snowflakes falling through a 2D space and accumulating at the bottom or on top of other flakes. It demonstrates gravity-driven particle movement and the formation of structured deposits.

**2. States:**
- `0` - Empty: Clear air.
- `1` - Snow: A snowflake in motion or accumulated.

**3. Neighborhood:**
This model does **not** use a standard spatial weights strategy. Instead, it computes relationships directly from the grid indices (e.g., checking the cell directly above or below in the `row-col` grid).

**4. Transition Rules:**
- **Generation:** Snowflakes appear at the top row with a probability `probability`.
- **Movement:** A snowy cell moves down if the cell below it is empty.
- **Accumulation:** A snowy cell stays in place if it is on the bottom row or if the cell below it is already occupied by snow.
- **Arrival:** An empty cell becomes snowy if the cell above it contains a snowflake that is moving down.

!!! note "Temporal Constraint"
    To allow flakes to reach the ground, the simulation time should be significantly larger than the grid height. A rule of thumb is `end_time > 2 * grid_height`.

**5. Usage Example:**
```python
from dissmodel.geo import vector_grid
from dissmodel.core import Environment
from dissmodel_ca.models import Snow

# Create a 20x20 grid
grid = vector_grid(dimension=(20, 20), resolution=1, attrs={"state": 0})

# Setup environment (steps > grid height)
env = Environment(end_time=60)

# Instantiate the Snow model
snow = Snow(gdf=grid, dim=20)

# Set the snowfall probability
snow.setup(probability=0.05)

# Run the simulation
env.run()
```

---

### Solid Diffusion

**1. Description:**
Simulates the atomic diffusion between two solids via a vacancy mechanism. Based on the NetLogo Solid Diffusion model, it shows how two different types of atoms eventually reach uniform mixing by randomly swapping positions with empty lattice sites (vacancies).

**2. States:**
- `0` - Atom Type 1: Initialized on the left half of the grid.
- `1` - Atom Type 2: Initialized on the right half of the grid.
- `2` - Vacancy: Empty site that allows atoms to move.

**3. Neighborhood:**
**Moore (Queen)** neighborhood (8 neighbors), calculated directly from grid indices.

**4. Transition Rules:**
This model uses a **sequential random sweep** rather than synchronous updates:
- At each step, every vacancy is processed in a shuffled order.
- Each vacancy selects one non-vacant neighbor at random.
- The vacancy and the chosen neighbor swap their states.

!!! note "Physical Correctness"
    The use of a sequential sweep and state swapping ensures that the number of atoms of each type remains constant, which is a fundamental physical requirement of diffusion simulations.

**5. Usage Example:**
```python
from dissmodel.geo import vector_grid
from dissmodel.core import Environment
from dissmodel_ca.models import SolidDiffusion

# Create a square grid (odd dimension ensures a clear middle column)
grid = vector_grid(dimension=(31, 31), resolution=1, attrs={"state": 0})

# Environment setup
env = Environment(end_time=500)

# Instantiate the model
sd = SolidDiffusion(gdf=grid, dim=31)

# Initialize the two solids separated by a central line of vacancies
sd.initialize()

# Run the simulation
env.run()
```

---

### Wolfram Elementary CA

**1. Description:**
Implements Stephen Wolfram's 256 elementary (1D) cellular automata. Although the logic is one-dimensional, it is visualized in 2D, where each row represents one generation. This allows for the visualization of the entire history of the automaton in a single image.

**2. States:**
- `0` - Dead / OFF
- `1` - Alive / ON

**3. Neighborhood:**
The neighborhood is **1D and temporal**: a cell's state depends on its own state and its two horizontal neighbors (left and right) from the **previous row** (previous generation).

**4. Transition Rules:**
The model uses a 3-bit lookup table derived from a rule number (0–255).
- Each possible 3-cell pattern (e.g., `110`, `010`) is mapped to a resulting state `0` or `1`.
- The horizontal boundaries wrap (toroidal), so the leftmost cell treats the rightmost cell as its neighbor.

**5. Usage Example:**
```python
from dissmodel.geo import vector_grid
from dissmodel.core import Environment
from dissmodel_ca.models import Wolfram

# For a classic pyramid shape with 55 generations
# We need a grid with 111 columns and 56 rows
grid = vector_grid(dimension=(111, 56), resolution=1, attrs={"state": 0})
env = Environment(end_time=55)

# Instantiate rule 90 (Sierpiński triangle)
wolfram = Wolfram(gdf=grid, final_time=55)
wolfram.setup(rule_number=90, final_time=55)

# Initialize with a single alive cell in the center of the first row
wolfram.initialize()

# Run the simulation
env.run()
```
