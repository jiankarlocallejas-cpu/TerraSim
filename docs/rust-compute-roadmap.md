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

**Exit gate:** passed in an offscreen Qt smoke check: the window constructed, all five pages switched, and model controls/layer references saved to a project file.

### 1. Numerical reference and D-infinity routing — reference gate passed

- Keep D∞ separate from the sediment/terrain update: it estimates direction and upslope contributing area from a DEM.
- State the depression policy explicitly. The current reference leaves flats and depressions terminal; it does not silently fill or breach them.
- Preserve projected map units and physical cell area, including non-square pixels.
- Test planar direction, nodata exclusion, terminals, input validation, and area conservation on synthetic grids.

**Checks already run:** 13 focused tests passed on single-cell, planar, rectangular-cell, nodata, random-surface, empty-domain, and invalid-input cases. A 64×64 Python reference run took about 0.52 s in the current environment. That is a diagnostic measurement, not a large-raster performance claim.

**Integration gate:** passed. The legacy workflow now accepts the source nodata value and both cell dimensions, excludes nodata from terrain statistics/derivatives, and passes them to D∞. The saved suite passes with the repository pytest configuration: 14 tests passed, 72% coverage for the focused modules.

### 2. Paper-aligned Python terrain model — reference gate passed

Implement the paper as a separate, small-grid reference path:

1. Compute the weighted multi-criteria susceptibility index from its input layers and explicit user-selected weights.
2. Compute metric-coordinate terrain gradients and sediment flux from the paper's transport law, including `α`, `β`, the diffusion tensor `D`, and critical slope `S_c`.
3. Update elevation with the sediment-flux divergence (Exner form) and an explicit, stability-limited time step.
4. Define nodata, no-flux/open-edge boundaries, units, and mass-balance accounting.

Do not invent calibrated coefficients. The paper does not provide enough calibration to turn soil or rainfall values into validated `α` and `β`; show provenance and keep exploratory controls adjustable until a defensible relationship is established.

**Checks run:** `backend/services/paper_model.py` now provides the weighted MCE overlay and conservative closed-boundary Exner reference update. It masks nodata, validates the tensor and coefficients, limits explicit timesteps, and advances without retaining a full time history. The focused checks cover flat and sloped surfaces, threshold/α/β response, anisotropy, stability rejection, adaptive substeps, nodata, and volume conservation. The router and solver tests pass: 32 cases. The current full suite passes 41 tests with 80% coverage across the focused modules.

**Remaining gate:** connect the solver to project/scenario settings in Qt, then validate it on raster inputs with explicit CRS, resolution, and parameter provenance.

### 3. GIS inputs and validation — metadata gate passed

- Inspect GeoTIFF metadata without loading its pixel array; preserve CRS, metric pixel dimensions, nodata, transform, and data type.
- Require a projected metre-based CRS and north-up grid; reject missing/geographic CRS and rotated grids with a clear reason.
- Compare CRS, dimensions, and affine transforms for DEM/criterion alignment before cell-wise combination.
- Save raster roles and refreshed metadata with the project; re-inspect source files when a project is reopened.

**Checks run:** 8 synthetic GeoTIFF tests and an offscreen Qt input/project round-trip test pass. The UI flags a shifted criterion raster and allows explicit DEM role assignment.

**Remaining gate:** load pixel arrays in the background after a memory preflight, run the model, and export a result raster.

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

The Qt shell passes an offscreen project/raster-role round trip. GeoTIFF preflight and raster alignment checks are connected to the Input Data page. The paper-aligned MCE and Exner reference are implemented, with the solver ready for Qt integration. The current temporary verification tree reports 41 passing tests and 80% coverage across the focused modules. Raster pixel loading, UI simulation, result export, large-raster runtime, out-of-core processing, and Rust acceleration remain unfinished.