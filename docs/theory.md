# Theory of Cellular Automata

Cellular Automata (CA) are discrete, abstract computational systems that have proven very useful as models to simulate complex systems where many simple components interact locally.

## A Brief History

The concept was originally proposed in the 1940s by **John von Neumann** and **Stanislaw Ulam**. Von Neumann was interested in the idea of "Self-Replicating Automata"—machines that could create copies of themselves.

However, CA became widely known in the 1970s through **John Conway's Game of Life**, which demonstrated how incredibly complex patterns (and even universal computation) could emerge from just a few simple rules.

## The 6 Core Components of CA

To define a Cellular Automaton, we need six fundamental elements:

1.  **Cellular Space (Grid)**: A collection of cells arranged in a specific geometry (e.g., a 2D grid, a hexagonal tiling, or even irregular polygons).
2.  **Cell States**: A finite set of discrete values that a cell can take (e.g., Alive/Dead, Forest/Burning/Burned).
3.  **Neighborhood**: For any given cell, the set of "nearby" cells that can influence its next state.
4.  **Transition Rules**: The logic that determines the next state of a cell based on its current state and the states of its neighbors.
5.  **Initial State**: The configuration of all cell states at time $t=0$.
6.  **Discrete Time**: The system evolves in discrete steps (ticks), where all cells are updated simultaneously.

## Neighborhoods: Moore vs. Von Neumann

In a regular 2D grid, two types of neighborhoods are most common:

*   **Von Neumann Neighborhood**: Includes the 4 immediate neighbors (North, South, East, West). In `dissmodel-ca`, this is often implemented using the **Rook** strategy.
*   **Moore Neighborhood**: Includes all 8 surrounding neighbors (including diagonals). In `dissmodel-ca`, this is implemented using the **Queen** strategy.

!!! note "Theory: Spatial Weights"
    In DisSModel-CA, we use the library `libpysal` to handle these relationships. We call them "weights" because they describe the strength (or existence) of a connection between two spatial units.

## Synchronization and the "Double Buffer"

One of the most critical aspects of CA theory is **simultaneity**. Every cell must update its state at the exact same time.

To achieve this in code, frameworks like DisSModel-CA maintain two copies of the cellular space:
1.  **Past Values**: Used as the input to calculate the transition rules.
2.  **Present/Future Values**: Where the results of the rules are stored for the next step.

Without this "double buffering," a cell updated early in a time step could incorrectly influence its neighbor's update in the same step, leading to non-deterministic behavior.
