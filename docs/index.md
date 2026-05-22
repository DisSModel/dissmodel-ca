# Welcome to DisSModel-CA

**DisSModel-CA** is a modular Python framework designed for **Spatially Explicit Dynamic Modeling**, specifically focusing on **Cellular Automata (CA)**.

Developed by the **LambdaGeo** research group at the **Federal University of Maranhão (UFMA)**, DisSModel-CA is part of a broader effort to provide modern, accessible tools for spatial simulation.

## Origins and Inspiration

The framework is heavily inspired by **TerraME** (Terra Modeling Environment). While TerraME historically relied on the TerraLib/Lua stack, DisSModel-CA transitions this power to the modern Python ecosystem:

*   **Dual-Substrate Approach**: Just like TerraME, DisSModel supports both Vector and Raster data.
*   **Modern Stack**: It leverages industry-standard libraries:
    *   **GeoPandas**: For vector-based cellular spaces.
    *   **NumPy**: For high-performance raster operations.
    *   **Libpysal**: For advanced spatial weights and neighborhood definitions.

## Why DisSModel-CA?

Traditional CA models are often implemented as fixed grids. DisSModel-CA allows for more flexible "Cellular Spaces" where cells can be irregular polygons (Vector) or traditional pixels (Raster), enabling more realistic geographical modeling.

!!! info "Target Audience"
    This documentation is written with a didactic tone, primarily aimed at undergraduate students and researchers starting their journey in spatial dynamic modeling.

---
*LambdaGeo - Laboratório de Geotecnologias, UFMA.*
