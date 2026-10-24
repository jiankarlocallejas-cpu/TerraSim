# TerraSim rebuild roadmap

## Product scope

TerraSim is a native Qt desktop terrain and erosion simulator. The target model is a sequence of terrain/sediment updates on a raster grid. It is not a fluid solver, and a 3D terrain view is not 3D CFD. A fluid model would be a separate project phase with its own equations, boundaries, validation data, and compute budget.

Keep the old USPED workflow available as a reference while the paper-aligned model is implemented as a separate path. Do not copy old parameter defaults or formulas into the new model unless their meanings, units, and derivation match.

## Architecture target

- **Qt/Python application:** projects, GIS input/output, validation, charts and maps, workflow controls.
- **Python reference solver:** readable equations and small-grid validation.
- **Rust numerical core:** measured hotspots after reference behavior is locked.
- **Python/Rust boundary:** a small PyO3/maturin extension. Pass whole arrays or tiles; never call Rust once per cell.

## Implementation sequence and exit gates

### 0. Desktop baseline — established

- Launch the native Qt window from `terrasim.py`, `run.bat`, and `run.sh`.
- Save and reopen a `.terrasim.json` project.
- Keep the web/API launch paths out of the desktop entry points.

**Exit gate:** an offscreen Qt smoke test can create the window, navigate pages, and round-trip a project.

### 1. Numerical reference and D-infinity routing — underway

- Keep D∞ separate from the sediment/terrain update: it estimates direction and upslope contributing area from a DEM.
- State the depression policy explicitly. The current reference leaves flats and depressions terminal; it does not silently fill or breach them.
- Preserve projected map units and physical cell area, including non-square pixels.
- Test planar direction, nodata exclusion, terminals, input validation, and area conservation on synthetic grids.

**Checks already run:** 13 focused tests passed on single-cell, planar, rectangular-cell, nodata, random-surface, empty-domain, and invalid-input cases. A 64×64 Python reference run took about 0.52 s in the current environment. That is a diagnostic measurement, not a large-raster performance claim.

**Remaining gate:** pass the source nodata value and both cell dimensions through the legacy workflow, then run the saved regression suite from the repository's normal test command.

### 2. Paper-aligned Python terrain model — next

Implement the paper as a separate, small-grid reference path:

1. Compute the weighted multi-criteria susceptibility index from its input layers and explicit user-selected weights.
2. Compute metric-coordinate terrain gradients and sediment flux from the paper's transport law, including `α`, `β`, the diffusion tensor `D`, and critical slope `S_c`.
3. Update elevation with the sediment-flux divergence (Exner form) and an explicit, stability-limited time step.
4. Define nodata, no-flux/open-edge boundaries, units, and mass-balance accounting.

Do not invent calibrated coefficients. The paper does not provide enough calibration to turn soil or rainfall values into validated `α` and `β`; show provenance and keep exploratory controls adjustable until a defensible relationship is established.

**Exit gate:** equation-by-equation tests on uniform terrain, a known planar gradient, threshold activation, `α`/`β` sensitivity, time-step stability, and sediment-volume balance.

### 3. GIS inputs and validation

- Load GeoTIFF metadata and arrays without guessing CRS, scale, nodata, or units.
- Require a projected CRS with linear units for metric gradients; warn or request reprojection for angular coordinates.
- Check raster dimensions, transforms, pixel sizes, alignment, nodata masks, and required inputs before a run.
- Keep source file paths and model-input choices in the project.

**Exit gate:** a tiny sample project loads, validates, saves, and reports every mismatch before simulation.

### 4. Connect the solver to Qt

- Persist the full model configuration and its provenance with each scenario.
- Run computation off the UI thread; provide progress, cancellation, clear errors, and a pre-run memory estimate.
- Show input/parameter summaries, time-step controls, and a terrain/erosion preview.
- Export final rasters and a run manifest; do not retain every time step in memory by default.

**Exit gate:** the sample project can run end-to-end, cancel cleanly, reopen results, and produce repeatable output.

### 5. Profile and bound memory

A faster kernel alone does not solve out-of-memory failures. Measure time and peak memory by stage, then:

- Estimate memory from grid size, cell types, work buffers, and retained outputs before starting.
- Reuse arrays and stream intermediate/final rasters to disk.
- Add window/tile processing with neighbor halos and consistent fluxes at tile edges.
- Expose a memory budget and select a small-grid mode for laptop validation.

**Exit gate:** tile and full-grid runs agree within a documented tolerance and pass the same conservation checks.

### 6. Migrate measured hotspots to Rust

- Profile the reference solver first; choose the hottest deterministic kernels.
- Add a typed PyO3/maturin extension while retaining a Python fallback.
- Port one kernel at a time and compare directions, fluxes, elevation change, mass balance, runtime, and peak memory.
- Keep precision changes opt-in until their error is measured.

**Exit gate:** Rust matches the reference on edge, nodata, flat, tile-boundary, and stress cases, and improves measured runtime or memory.

### 7. Package and document

- Ship a Windows desktop install/launch path with a clear dependency story.
- Include a small demonstration dataset, model assumptions, coefficient provenance, and known limitations.
- Run the documented checks on a clean environment.

**Exit gate:** a clean machine can install, open the sample project, run it, and export results.

### 8. Consider fluid flow separately

If water-flow simulation is later required, specify whether the target is depth-averaged shallow water or full 3D free-surface flow. Define governing equations, initial/boundary conditions, friction/turbulence, sediment coupling, stability limits, and reference data first. Do not call the current terrain-evolution model CFD-capable.

## Memory-first requirements

- Avoid full per-timestep histories in RAM.
- Reuse buffers and avoid copies at the Python/Rust boundary.
- Keep D∞ receiver state compact; any tiled accumulation method must preserve upstream dependencies across tile boundaries.
- Benchmark small, medium, and stress cases and publish grid dimensions, machine, runtime, and peak memory.

## References

- Tarboton (1997), [A new method for the determination of flow directions and upslope areas in grid digital elevation models](https://doi.org/10.1029/96WR03137).
- Paper supplied for this rebuild: `MCS_TERRASIM_revised.pdf`.

## Current status

The Qt shell and project persistence are present. The D∞ reference router passes focused synthetic-grid checks and regression tests are now in the branch. The router remains Python-loop based; no paper-aligned solver has been implemented or connected to the Qt UI. Large-raster runtime, out-of-core processing, and Rust acceleration remain unverified.