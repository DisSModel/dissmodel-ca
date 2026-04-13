# dissmodel-ca

Cellular Automata (CA) extension for `dissmodel`.

This library provides several cellular automata models implemented using the `dissmodel` engine, including both vector (GeoDataFrame-based) and raster (NumPy-based) versions.

## Features

- **Classic Models:** Game of Life, Forest Fire, Anneal, Snow, etc.
- **Dual Engine:** Support for both vector and raster backends.
- **Streamlit Apps:** Interactive explorers for all implemented models.
- **CLI Tools:** Quick run and visualization of simulations.

## Installation

```bash
pip install .
```

## Usage

### Using the Models

```python
from dissmodel_ca.models import GameOfLife
from dissmodel.geo import vector_grid
from dissmodel.core import Environment

# Setup environment and grid
env = Environment(end_time=10)
gdf = vector_grid(dimension=(20, 20))

# Initialize and run model
model = GameOfLife(gdf=gdf)
model.initialize()
env.run()
```

### Running Streamlit Apps

```bash
streamlit run src/dissmodel_ca/streamlit/ca_all.py
```

### CLI

```bash
python -m dissmodel_ca.cli.ca_game_of_life
```

## Structure

- `src/dissmodel_ca/models/`: Core CA model implementations.
- `src/dissmodel_ca/streamlit/`: Streamlit web applications.
- `src/dissmodel_ca/cli/`: Command-line interfaces.
- `notebooks/`: Example Jupyter notebooks.
