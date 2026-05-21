# dissmodel-ca

**Cellular Automata (CA) extension for `dissmodel`.**

This library provides a collection of cellular automata models implemented using the `dissmodel` engine. It showcases the power of the framework's dual-substrate architecture, offering both vector (GeoDataFrame) and raster (NumPy) versions of classic and research models.

## 🌟 Features

- **Classic & Research Models:** Game of Life, Forest Fire (Probabilistic), Anneal, Snow, and more.
- **Dual Substrate:** Seamlessly switch between vector precision and raster performance.
- **Interactive Dashboards:** Built-in Streamlit apps for real-time parameter exploration.
- **Jupyter Notebooks:** 15+ educational notebooks with step-by-step scientific explanations.

## ⚙️ Installation

```bash
pip install .
```

## 🚀 Usage

### 1. Simple Script (Quick Start)
For a quick run with default parameters and visual output:

```bash
python examples/cli/ca_game_of_life.py
```

### 2. Interactive Streamlit App
Explore all models via a reactive web interface:

```bash
streamlit run examples/streamlit/ca_all.py
```

### 3. Jupyter Notebooks (Didactic)
The best way to learn about each model is through our educational notebooks in Portuguese:

```bash
jupyter lab examples/notebooks/ca_game_of_life.ipynb
```

---

## 📂 Repository Structure

- **`src/dissmodel_ca/models/`**: Core CA implementations (the "Science" layer).
- **`examples/notebooks/`**: 15+ didactic notebooks (Intro, Concepts, Rules, Execution).
- **`examples/cli/`**: Simplified, self-contained scripts for quick testing.
- **`examples/streamlit/`**: Reactive UI components and apps.

---

## 🛠️ Included Models

| Model | Substrate | Description |
|:---|:---|:---|
| `GameOfLife` | Vector / Raster | Classic Conway's simulation. |
| `FireModel` | Vector / Raster | Forest fire spread with probabilistic regrowth. |
| `Snow` | Vector | Snowfall accumulation and gravity dynamics. |
| `Growth` | Vector | Stochastic radial growth. |
| `Anneal` | Vector | Binary system relaxation via majority-vote rule. |
| `Excitable` | Vector | Excitable medium waves (spiral/ring patterns). |
| `Parasit` | Vector | Host-parasit spatial dynamics. |
| `Interspecific` | Vector | Grass species competition model. |
