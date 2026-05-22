# Complete Simulation Examples

This section provides comprehensive, step-by-step guides for running simulations in DisSModel-CA. These examples are designed to help undergraduate students understand the full pipeline: from setting up the cellular space to visualizing the results with appropriate color maps.

---

## 1. Ecological Competition: Interspecific Species

This example replicates the model by Silvertown et al. (1992). It simulates how five species of grass compete for space. We will use a **Vector** approach and a specialized visualization.

### Step 1: Create the Cellular Space
We create a 40x40 grid, which is the standard size used in the original research to allow for distinct horizontal bands.

```python
from dissmodel.geo import vector_grid

# Create a 40x40 vector grid.
# The 'state' attribute will hold the species ID (0-4).
grid = vector_grid(dimension=(40, 40), resolution=1, attrs={"state": 0})
```

### Step 2: Configure the Environment
The environment controls the time-stepping logic.

```python
from dissmodel.core import Environment

# We run for 200 steps to allow patterns to emerge.
env = Environment(end_time=200)
```

### Step 3: Instantiate and Initialize the Model
We choose "ModelA", which starts with five horizontal bands of species.

```python
from dissmodel_ca.models import InterspecificCompetition

# Instantiate the model with the initial arrangement 'ModelA'
ic = InterspecificCompetition(gdf=grid, displacement="ModelA")

# initialize() populates the 'state' column based on the ModelA bands
ic.initialize()
```

### Step 4: Visualization (Color Maps)
To see the results clearly, we map each species ID to a distinct color.

```python
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# Define colors for the 5 species:
# 0:Lolium (Green), 1:Agrostis (Red), 2:Holcus (Blue), 
# 3:Poa (Yellow), 4:Cynosurus (Purple)
colors = ["#2ecc71", "#e74c3c", "#3498db", "#f1c40f", "#9b59b6"]
cmap = ListedColormap(colors)

# Plot the initial state
grid.plot(column="state", cmap=cmap)
plt.title("Initial Species Distribution (Model A)")
plt.show()
```

### Step 5: Run and Analyze
```python
env.run()

# Plot the final state after 200 steps
grid.plot(column="state", cmap=cmap)
plt.title("Final Species Distribution after 200 steps")
plt.show()
```

---

## 2. High-Performance Forest Fire (Raster)

When dealing with large landscapes (e.g., 500x500 cells), the **Raster** approach is preferred. This example shows how to use the vectorized `FireModel`.

### Step 1: Setup the Raster Backend
Instead of a GeoDataFrame, we use a `RasterBackend` which holds raw NumPy arrays.

```python
from dissmodel.geo.raster.backend import RasterBackend

# A 200x200 grid (40,000 cells)
backend = RasterBackend(shape=(200, 200))
```

### Step 2: Initialize with Probabilities
We can use NumPy to quickly set up our initial conditions.

```python
import numpy as np
from dissmodel_ca.models.fire_model import FireState

# Set 2% of the forest on fire randomly
rng = np.random.default_rng(42)
initial_state = np.where(
    rng.random((200, 200)) < 0.02, 
    FireState.BURNING, 
    FireState.FOREST
)

# Store the data in the backend
backend.set("state", initial_state.astype(np.int8))
```

### Step 3: Run the Simulation
The environment remains the same regardless of the substrate (Vector/Raster).

```python
from dissmodel.core import Environment
from dissmodel_ca.models import FireModel

env = Environment(start_time=1, end_time=100)
fire = FireModel(backend=backend)

# The simulation runs using vectorized rule logic
env.run()
```

### Step 4: Visualization
For Raster data, we can use `imshow` for maximum performance.

```python
# Map: 0:Forest (Green), 1:Burning (Orange), 2:Burned (Gray)
fire_cmap = ListedColormap(["#27ae60", "#e67e22", "#7f8c8d"])

plt.imshow(backend.get("state"), cmap=fire_cmap)
plt.colorbar(ticks=[0, 1, 2], label="0:Forest, 1:Burning, 2:Burned")
plt.title("Forest Fire Spread (Raster)")
plt.show()
```

---

## Summary Checklist
Every `dissmodel-ca` simulation follows this flow:
1. **Space**: Define your `vector_grid` (GDF) or `RasterBackend` (Arrays).
2. **Environment**: Set the duration with `Environment(end_time=X)`.
3. **Model**: Instantiate your model class (passing the space).
4. **Initialize**: Call `initialize()` or set states manually.
5. **Run**: Trigger the logic with `env.run()`.
6. **Visualize**: Plot the final `gdf` or `backend` array.
