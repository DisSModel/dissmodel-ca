# DisSModel-CA Architecture

DisSModel-CA maps the abstract theory of Cellular Automata into a modular and extensible Python class structure.

## Mapping Theory to Code

| CA Component | Python / DisSModel Concept |
| :--- | :--- |
| **Cellular Space** | `geopandas.GeoDataFrame` (Vector) or `numpy.ndarray` (Raster) |
| **Cell State** | A column in the GeoDataFrame (e.g., `gdf['state']`) |
| **Neighborhood** | `libpysal.weights.W` object |
| **Transition Rules** | The `rule()` method in the `CellularAutomaton` class |
| **Discrete Time** | The `Environment` class and the `step()` loop |

## The `CellularAutomaton` Base Class

The heart of the framework is the `CellularAutomaton` class. To create your own model, you typically inherit from this class and implement three main methods:

1.  **`setup()`**: Used to define the neighborhood strategy (e.g., Queen or Rook) and model parameters.
2.  **`initialize()`**: Defines the initial state of the grid (e.g., random distribution or specific patterns).
3.  **`rule(idx)`**: The core logic. It receives the index of a cell and returns the value it should have in the next time step.

## Spatial Weights with Libpysal

DisSModel-CA leverages `libpysal` to manage complex spatial relationships. This is what allows the framework to go beyond simple grids.

*   **`Queen`**: Used for Moore neighborhoods (8 neighbors).
*   **`Rook`**: Used for Von Neumann neighborhoods (4 neighbors).

!!! tip "Irregular Cells"
    Because we use GeoPandas and Libpysal, you can run a "Cellular Automaton" on a map of cities or census tracts! The `Queen` weight will simply find all polygons that share a vertex or edge with the target cell.

## Execution Flow

When you run a model, DisSModel-CA performs these steps:
1.  **Setup**: Builds the neighborhood graph.
2.  **Initialize**: Sets the starting values for all cells.
3.  **Step Loop**:
    *   Iterates through every cell in the space.
    *   Calls `rule(idx)` for each cell.
    *   Collects all new states.
    *   **Synchronize**: Updates all cells simultaneously once all rules have been calculated.
