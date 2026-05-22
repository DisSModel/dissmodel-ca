# DisSModel-CA Architecture

DisSModel-CA maps the abstract theory of Cellular Automata into a modular and extensible Python class structure.

## Dual Modeling Approaches: Vector vs. Raster

One of the core strengths of DisSModel-CA is the ability to choose between two different substrates for your Cellular Automata, depending on your needs for flexibility or performance.

### 1. Vector Approach (`CellularAutomaton`)
The **Vector approach** uses `geopandas.GeoDataFrame` as the underlying data structure. 
- **Mechanism**: The transition `rule(idx)` is called once per cell, per time step.
- **Flexibility**: Highly flexible. It supports irregular polygons (like municipalities or census tracts) and complex spatial weights via `libpysal`.
- **Readability**: Logic is expressed from the perspective of a single cell ("If I am alive and have X neighbors..."), making it very intuitive for students and researchers.

### 2. Raster Approach (`RasterCellularAutomaton`)
The **Raster approach** uses `numpy` arrays and a specialized `RasterBackend`.
- **Mechanism**: The transition `rule(arrays)` is called once per time step for the *entire grid*. It utilizes vectorized operations (NumPy) to calculate the next state of all cells simultaneously.
- **Performance**: Optimized for large, regular grids. It can be orders of magnitude faster than the vector approach for high-resolution simulations.
- **Complexity**: Requires expressing rules as matrix operations (e.g., focal sums and boolean masks).

---

## Illustration: Game of Life

To understand the difference, consider the implementation of Conway's Game of Life in both architectures:

=== "Vector (Cell-by-Cell)"
    ```python
    # Logic: "What is my next state?"
    def rule(self, idx):
        state = self.gdf.loc[idx, "state"]
        # Count live neighbors for THIS specific cell
        live_neighbors = (self.neighbor_values(idx, "state") == 1).sum()

        if state == 1:
            return 1 if 2 <= live_neighbors <= 3 else 0
        return 1 if live_neighbors == 3 else 0
    ```

=== "Raster (Full-Grid Vectorized)"
    ```python
    # Logic: "What is the next state for all cells at once?"
    def rule(self, arrays):
        state = arrays["state"]
        # Calculate neighbor counts for the whole grid using focal sums
        neighbors = self.backend.focal_sum_mask(state == 1)

        survive = (state == 1) & np.isin(neighbors, [2, 3])
        born    = (state == 0) & (neighbors == 3)

        return {"state": np.where(survive | born, 1, 0).astype(np.int8)}
    ```

---

## Documentation Strategy

While DisSModel-CA provides high-performance raster implementations for many classic models, our [Model Reference](reference.md) primarily uses the **Vector Approach** for its examples and logic explanations.

**Why focus on Vector?**
1. **Academic Clarity**: The cell-by-cell logic more closely mirrors how CA rules are traditionally taught in theoretical modeling.
2. **Standardization**: It allows us to present a unified API that works across different spatial scales, from simple grids to complex geographical shapes.
3. **Ease of Modification**: It is generally easier for a researcher to modify a Pythonic `if/else` block in a vector `rule()` than to refactor a complex NumPy mask in a raster implementation.

---

## Mapping Theory to Code

| CA Component | Vector Mapping | Raster Mapping |
| :--- | :--- | :--- |
| **Cellular Space** | `geopandas.GeoDataFrame` | `numpy.ndarray` |
| **Cell State** | GDF Column (e.g., `gdf['state']`) | Array in `RasterBackend` |
| **Neighborhood** | `libpysal.weights.W` | Adjacency Windows (Focal) |
| **Transition Rules** | `rule(idx)` | `rule(arrays)` |
| **Discrete Time** | `Environment` step loop | `Environment` step loop |

## Execution Flow (Vector)

When you run a vector model, DisSModel-CA performs these steps:
1.  **Setup**: Builds the neighborhood graph using `libpysal`.
2.  **Initialize**: Sets the starting values for all cells.
3.  **Step Loop**:
    *   Iterates through every cell in the space.
    *   Calls `rule(idx)` for each cell.
    *   Collects all new states.
    *   **Synchronize**: Updates all cells simultaneously once all rules have been calculated (ensuring synchronous update).
