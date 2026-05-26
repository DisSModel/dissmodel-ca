"""
Cellular Automata Explorer — Streamlit (Interactive & Didactic)
==============================================================
Dynamically loads all cellular automaton models from ``dissmodel_ca.models``
and lets the user choose, configure, and run any of them from a single
interface.

This version is optimized for performance and interactivity, using raster
visualization and step-by-step animation.

Usage
-----
    streamlit run examples/streamlit/ca_all_iter.py
"""
from __future__ import annotations

import inspect
import time
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

import dissmodel_ca.models as ca_models
from dissmodel.core import Environment
from dissmodel.geo import CellularAutomaton, vector_grid
from dissmodel.visualization.widgets import display_inputs

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="CA Explorer (Didactic)", layout="wide")
st.title("Cellular Automata Explorer (dissmodel)")

# ---------------------------------------------------------------------------
# Discover models
# ---------------------------------------------------------------------------
model_classes: dict[str, type] = {
    name: cls
    for name, cls in inspect.getmembers(ca_models, inspect.isclass)
    if issubclass(cls, CellularAutomaton)
    and cls is not CellularAutomaton
    and not inspect.isabstract(cls)
}

# ---------------------------------------------------------------------------
# Sidebar — configuration
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Simulation Config")
    model_name = st.selectbox("Model", list(model_classes.keys()))
    grid_size  = st.slider("Grid size", 10, 100, 30)
    steps      = st.slider("Max steps", 1, 500, 50)
    
    st.header("Visualization")
    cmap_name  = st.selectbox(
        "Colormap",
        ["viridis", "tab10", "plasma", "Greens", "Reds", "Blues", "coolwarm", "binary"],
    )
    anim_speed = st.slider("Animation Speed (fps)", 1, 30, 10)
    
    st.markdown("---")
    st.header("Design & Controls")
    col_run, col_step = st.columns(2)
    run_btn = col_run.button("▶ Run", use_container_width=True)
    step_btn = col_step.button("⏭️ Step", use_container_width=True)
    
    col_reset, col_clear = st.columns(2)
    reset_btn = col_reset.button("🔄 Reset", use_container_width=True)
    clear_btn = col_clear.button("🗑️ Clear", use_container_width=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state_key(name: str, size: int) -> str:
    return f"gdf_state_{name}_{size}"

def _possible_states(model: CellularAutomaton) -> list[int]:
    if hasattr(model, "states") and isinstance(model.states, (list, tuple)):
        return sorted(int(s) for s in model.states)
    
    import enum
    module = inspect.getmodule(model.__class__)
    if module:
        for _, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, enum.IntEnum):
                return sorted([int(e) for e in obj])
    
    states = sorted(int(v) for v in model.gdf["state"].unique())
    if not states or (len(states) == 1 and states[0] == 0):
        return [0, 1]
    return states

def render_grid(gdf, size, cmap_name, plot_area, title=""):
    try:
        matrix = gdf["state"].values.reshape((size, size))
        matrix = matrix[::-1, :] # Flip Y
    except ValueError:
        plot_area.error("Grid dimension mismatch. Try resetting.")
        return

    fig, ax = plt.subplots(figsize=(6, 6))
    p_states = _possible_states(model)
    vmin, vmax = min(p_states), max(p_states)
    if vmin == vmax: vmax = vmin + 1
    
    ax.imshow(matrix, cmap=cmap_name, interpolation='nearest', vmin=vmin, vmax=vmax)
    ax.axis('off')
    if title:
        ax.set_title(title)
    
    plot_area.pyplot(fig)
    plt.close(fig)

# ---------------------------------------------------------------------------
# Setup Environment & Model
# ---------------------------------------------------------------------------
env = Environment(start_time=0, end_time=steps)
gdf = vector_grid(dimension=(grid_size, grid_size), resolution=1, attrs={"state": 0})

ModelClass = model_classes[model_name]
model = ModelClass(gdf=gdf, dim=grid_size, start_time=0, end_time=steps)

# Sidebar model parameters
with st.sidebar:
    st.markdown(f"**{model_name} Parameters**")
    display_inputs(model, st.sidebar)

# State management
state_key = _state_key(model_name, grid_size)
if "last_config" not in st.session_state or st.session_state["last_config"] != (model_name, grid_size) or reset_btn:
    model.initialize()
    st.session_state[state_key] = gdf["state"].copy()
    st.session_state["step_count"] = 0
    st.session_state["last_config"] = (model_name, grid_size)
elif clear_btn:
    gdf["state"] = 0
    st.session_state[state_key] = gdf["state"].copy()
    st.session_state["step_count"] = 0
else:
    gdf["state"] = st.session_state[state_key]

# ---------------------------------------------------------------------------
# Main UI Layout
# ---------------------------------------------------------------------------
col_map, col_paint = st.columns([2, 1])

with col_map:
    plot_area = st.empty()
    status_area = st.empty()

# ---------------------------------------------------------------------------
# Paint Logic
# ---------------------------------------------------------------------------
with col_paint:
    st.header("🖌️ Paint Cells")
    paint_enabled = st.toggle("Enable Paint Mode", value=True)
    
    if paint_enabled:
        p_states = _possible_states(model)
        c1, c2 = st.columns(2)
        px = c1.number_input("Col (X)", 0, grid_size - 1, 0)
        py = c2.number_input("Row (Y)", 0, grid_size - 1, 0)
        pv = st.selectbox("Value", options=p_states, index=min(1, len(p_states)-1))
        
        if st.button("Apply Cell", use_container_width=True):
            cell_id = f"{px}-{py}"
            gdf.at[cell_id, "state"] = pv
            st.session_state[state_key] = gdf["state"].copy()
            st.toast(f"Cell ({px}, {py}) set to {pv}")
            
        st.markdown("---")
        fv = st.selectbox("Fill Value", options=p_states, index=0)
        if st.button("Fill Entire Grid", use_container_width=True):
            gdf["state"] = fv
            st.session_state[state_key] = gdf["state"].copy()

# ---------------------------------------------------------------------------
# Initial Render
# ---------------------------------------------------------------------------
render_grid(gdf, grid_size, cmap_name, plot_area)
status_area.write(f"**Step:** {st.session_state['step_count']}")

# ---------------------------------------------------------------------------
# Execution (Run / Step)
# ---------------------------------------------------------------------------
if step_btn:
    model.execute()
    st.session_state["step_count"] += 1
    st.session_state[state_key] = gdf["state"].copy()
    st.rerun()

if run_btn:
    for t in range(steps):
        model.execute()
        st.session_state["step_count"] += 1
        render_grid(gdf, grid_size, cmap_name, plot_area, title=f"Running... Step {st.session_state['step_count']}")
        status_area.write(f"**Step:** {st.session_state['step_count']}")
        st.session_state[state_key] = gdf["state"].copy()
        time.sleep(1.0 / anim_speed)
    st.success(f"Simulation finished at step {st.session_state['step_count']}")
