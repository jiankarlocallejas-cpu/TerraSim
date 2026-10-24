# TerraSim compute migration roadmap

## Target architecture

- **Qt/Python application:** project files, dialogs, GIS input/output, plotting, and workflow orchestration.
- **Rust numerical core:** measured hot kernels and, later, the paper-aligned terrain/sediment solver.
- **Python/Rust boundary:** a small native extension built with PyO3 and maturin. Keep arrays and batches at the boundary; avoid per-cell Python/Rust calls.

The migration is incremental. Existing Python code stays available as a reference until each Rust component has matching units, behavior, and numerical checks.

## Memory-first requirements

A faster kernel alone will not solve out-of-memory failures. The compute design must also:

1. Estimate peak memory from raster dimensions, cell types, working arrays, and number of retained time steps before a run.
2. Process rasters in windows/tiles with neighbor halos for derivative stencils.
3. Stream intermediate and output rasters to disk instead of retaining full histories in RAM.
4. Reuse buffers and avoid copies at the Python/Rust boundary.
5. Expose a memory budget and report tile size, estimated peak usage, progress, and cancellation.
6. Provide a small-grid mode so the model can be checked on a laptop without loading a city-scale dataset.

Tiling must preserve boundary behavior and fluxes across tile edges. Any precision reduction must be measured against reference runs; it must not be assumed safe merely to save memory.

## Staged migration

### 1. Establish reference behavior

Document the equations, parameter units, coordinate/grid conventions, boundary conditions, and expected outputs from the paper and recovered code. Use small synthetic DEMs and reduced real-data windows as reference cases. Record run time and peak memory for each case.

### 2. Profile and bound memory

Measure where time and memory go in the Python workflow. Start Rust work with an isolated, deterministic hotspot (for example raster normalization, gradients, or flux divergence) only after profiling confirms it is worth moving.

### 3. Add the Rust extension

Create a mixed Rust/Python package using PyO3 and maturin. Keep the public boundary narrow and typed; preserve the Qt UI and Python geospatial adapters. Keep a Python fallback while the extension is optional during development.

### 4. Migrate one kernel at a time

For each kernel, compare Rust with the Python reference on identical small inputs, including edge cells, nodata, flat terrain, and tile boundaries. Benchmark both runtime and peak memory. Replace a Python kernel only after numerical behavior is understood.

### 5. Finish and evaluate D-infinity routing

The previous prototype attempted D-infinity (D∞) routing but did not finish it. Treat it as a DEM-based flow-direction and upslope-contributing-area method: it selects a steepest-downslope angle over triangular facets and apportions contributing area to downslope cells. It is a terrain-routing algorithm, not a fluid dynamics solver. Compare its direction and accumulation behavior with established reference cases before using its outputs in a model. Tiled accumulation needs special care because flow dependencies cross tile boundaries.

Reference: Tarboton (1997), [A new method for the determination of flow directions and upslope areas in grid digital elevation models](https://doi.org/10.1029/96WR03137).

### 6. Implement the paper-aligned terrain model

Implement the paper's susceptibility index and sediment-flux/Exner update as a distinct model path. The paper describes terrain evolution from sediment-flux divergence; that is not a water-flow CFD solver. Do not wire coefficients from the older USPED implementation into the paper's equation without an explicit derivation.

### 7. Add fluid-flow simulation as a separate scope

If TerraSim should simulate water flow as CFD, specify the governing equations and coupling separately. A depth-averaged 2D shallow-water model is a different scope from a full 3D free-surface flow solver. Both need boundary/initial conditions, friction/turbulence choices, coupling to sediment transport, stability controls, and suitable validation data. “3D” terrain rendering alone does not mean 3D CFD.

## Verification gates

Before describing a solver as CFD-capable, document the solved equations, spatial and time discretization, boundary conditions, conservation behavior, stability limits, and benchmark/validation cases. Compare mass balance, grid and time-step sensitivity, and results against published or measured reference cases. Until then, label results as exploratory terrain/erosion simulations.

## Current project status

The Qt shell has exploratory relative α and β controls and project persistence. They are not yet connected to the simulation pipeline. Soil erodibility and critical-shear parameters may support sourced recommendations, but no direct conversion to the paper's α and β is defined.
