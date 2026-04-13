# dissmodel-ca

**Cellular Automata (CA) extension for `dissmodel`.**

This library provides a collection of cellular automata models implemented using the `dissmodel` engine. It showcases the power of the framework's dual-substrate architecture, offering both vector (GeoDataFrame) and raster (NumPy) versions of classic and research models.

## 🌟 Features

- **Classic & Research Models:** Game of Life, Forest Fire (Probabilistic), Anneal, Snow, and more.
- **Dual Substrate:** Seamlessly switch between vector precision and raster performance.
- **Interactive Dashboards:** Built-in Streamlit apps for real-time parameter exploration.
- **Experiment Tracking:** Professional-grade executors with built-in telemetry and JSON reporting.

## ⚙️ Installation

```bash
pip install .
```

## 🚀 Usage

### 1. Simple Script (Quick Start)
For a quick run with default parameters and visual output:

```bash
python -m dissmodel_ca.cli.ca_game_of_life
```

### 2. Model Executor (Production/Research)
Use the **Executor** for automated runs, cloud integration, and full experiment tracking (generates SHA256 checksums and profiling reports):

```bash
python src/dissmodel_ca/executor/ca_gol_vector_executor.py run \
  --input "synthetic" \
  --param grid_size=30 \
  --param end_time=50
```

### 3. Interactive Streamlit App
Explore all models via a reactive web interface:

```bash
streamlit run src/dissmodel_ca/streamlit/ca_all.py
```

---

## 📂 Repository Structure

- **`dissmodel_ca/models/`**: Core CA implementations (the "Science" layer).
- **`dissmodel_ca/executor/`**: Standardized executors for experiment tracking and reproducibility.
- **`dissmodel_ca/cli/`**: Simplified, self-contained scripts for quick testing.
- **`dissmodel_ca/streamlit/`**: Reactive UI components and apps.

---

## 🛠️ Included Models

| Model | Substrate | Description |
|:---|:---|:---|
| `GameOfLife` | Vector / Raster | Classic Conway's simulation. |
| `FireModel` | Vector / Raster | Forest fire spread with probabilistic regrowth. |
| `Snow` | Vector | Snowfall accumulation and gravity dynamics. |
| `Growth` | Vector | Stochastic radial growth. |
| `Anneal` | Vector | Binary system relaxation via majority-vote rule. |

---

## ⚖️ License

MIT © 2026 [LambdaGeo — UFMA](https://github.com/LambdaGeo)
