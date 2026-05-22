# Model Examples

In this section, we analyze how two classic models are implemented using the DisSModel-CA framework.

## 1. Conway's Game of Life

The Game of Life is the quintessential CA. It operates on a 2D grid where each cell is either **Alive (1)** or **Dead (0)**.

### The Rules
- **Survival**: A live cell with 2 or 3 live neighbors stays alive.
- **Death**: A live cell with < 2 (isolation) or > 3 (overpopulation) neighbors dies.
- **Birth**: A dead cell with exactly 3 live neighbors becomes alive.

### Implementation Logic

```python
class GameOfLife(CellularAutomaton):
    def setup(self) -> None:
        # We use Queen strategy for a Moore Neighborhood (8 neighbors)
        self.create_neighborhood(strategy=Queen, use_index=True)

    def rule(self, idx: Any) -> int:
        # 1. Get current state of the cell
        state = self.gdf.loc[idx, self.state_attr]
        
        # 2. Count live neighbors
        live_neighbors = (self.neighbor_values(idx, self.state_attr)).sum()

        # 3. Apply Conway's logic
        if state == 1:
            return 1 if 2 <= live_neighbors <= 3 else 0
        return 1 if live_neighbors == 3 else 0
```

!!! info "Step-by-Step"
    1.  **`setup`**: Defines that each cell looks at its 8 surrounding neighbors.
    2.  **`self.neighbor_values(idx, ...)`**: This is a powerful helper that automatically finds all neighbors of `idx` and returns their current values as a NumPy array.
    3.  **Summing**: Since "Alive" is represented by `1`, summing the neighbor values gives us the exact count of live neighbors.

---

## 2. Fire in the Forest Model

This model simulates the spread of fire through a forest. It uses 3 discrete states.

### The States
*   **FOREST (0)**: Green trees, ready to burn.
*   **BURNING (1)**: Currently on fire.
*   **BURNED (2)**: Ashes, cannot burn again.

### The Rules
1.  A **Burning** cell always becomes **Burned** in the next step.
2.  A **Forest** cell becomes **Burning** if at least one of its neighbors is burning.
3.  A **Burned** cell remains **Burned**.

### Implementation Logic

```python
class FireModel(CellularAutomaton):
    def setup(self, initial_fire_density: float = 0.05) -> None:
        # We use Rook strategy for a Von Neumann Neighborhood (4 neighbors)
        self.create_neighborhood(strategy=Rook, use_index=True)

    def rule(self, idx: Any) -> int:
        state = self.gdf.loc[idx, self.state_attr]

        # Rule 1: Burning becomes Burned
        if state == FireState.BURNING:
            return FireState.BURNED

        # Rule 2: Forest catches fire if a neighbor is burning
        if state == FireState.FOREST:
            # Check if any neighbor is in the BURNING state
            if (self.neighbor_values(idx, self.state_attr) == FireState.BURNING).any():
                return FireState.BURNING

        # Rule 3: Otherwise, stay the same (Forest stays Forest, Burned stays Burned)
        return state
```

!!! warning "Neighborhood Difference"
    Notice that while Game of Life uses the `Queen` neighborhood (8 neighbors), the Fire Model typically uses `Rook` (4 neighbors). DisSModel-CA makes it trivial to swap these behaviors by just changing the strategy in the `setup()` method.
