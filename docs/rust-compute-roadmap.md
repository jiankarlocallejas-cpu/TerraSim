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

### 4. Connect the solver to Qt — run/export gate passed; saved-run gate remains

- Persist model settings and input roles in the project.
- Load rasters and compute away from the UI thread; expose progress and cancellation checkpoints.
- Estimate memory before loading pixels and enforce the selected budget.
- Summarize run diagnostics and export final elevation and susceptibility rasters.
- Keep a run's input and coefficient provenance available for later review.

**Checks run:** the Qt worker loads synthetic aligned GeoTIFFs, calculates a weighted MCE layer, advances the DEM with the Exner reference, updates the Results page, and exports both outputs with source CRS, transform, and dimensions. A second offscreen Qt check requests cancellation by closing the application during a worker run and confirms that the window waits for the worker to stop before destroying its thread. With the Rust extension installed, the current Windows CI run passes 78 Python/Qt tests and 3 pure Rust tests.

**Saved-run gate:** passed. The Results page writes and reopens a versioned `.terrasim-run.json` file containing source paths and raster metadata, actual coefficients and slider multipliers, run diagnostics, coefficient-provenance notes, and exported output paths. The write is atomic. Reopening restores the report but does not reload raster arrays; the record is deliberately small and references output files by path.

**Remaining gate:** add a spatial preview. Scenarios remains a placeholder.

### 5. Profile and bound memory — tiled execution gate passed; out-of-core remains

The full-grid path updates terrain in place using bounded row scratch rather than retaining a second full update grid. A Python tiled path evaluates the same stencil in windows with two-cell halos. Each simulation step first reduces the stability bound across all tile cores, then computes the update pass with one globally conservative timestep. Cancellation during an incomplete tile pass discards that partial step and returns the last complete terrain.

The desktop offers Automatic, Full grid, and tiled 256/512/1024 modes. Automatic uses the full-grid path if its estimate fits the selected budget; otherwise it selects the largest configured tile size whose estimate fits. The selected and actual compute mode is persisted in the project and run record.

**Parity gate:** passed on synthetic 1024×1024, 10-step input. Full-grid and tiled 512×512 outputs were exactly equal (maximum difference 0.0), with the same step count, stable timestep and maximum step change, and zero mass error. Other tile sizes, nodata holes, masks, boundary halos, invalid sizes, and cancellation also have test coverage.

**Memory/runtime diagnostic:** in one local Windows/Python 3.12 process comparison on that case, working-set growth was about 180–181 MiB for full grid and 61.2 MiB for tiled 512×512 (about 66% lower). Full grid took about 3.06 s and tiled execution about 6.48 s. Tiling is a memory tradeoff, not a speed improvement. These measurements are one machine and synthetic workload. The selected tile estimate was about 129 MiB, intentionally above measured process growth.

**Important limit:** tiled solver windows only its stencil work. The Qt worker still loads the full DEM and criterion arrays, creates a full susceptibility array, and returns full output arrays for previews and export. Large inputs can therefore still exceed RAM despite a small tile. The tile memory budget is an estimate, not an OS-level guarantee.

**Next gate — true disk-backed raster processing:** read aligned GeoTIFF windows; store step state in temporary raster files or memory-mapped arrays; preserve one global CFL reduction per step; atomically advance only after a complete step; stream final outputs and bounded previews. Validate exact or documented tolerance-based parity, nodata and edge behavior, cancellation cleanup, mass conservation, and measured peak memory before calling this out-of-core.

### 6. Migrate measured hotspots to Rust — first kernel gate passed; migration continues

The first profiled hotspot was the per-step sediment-flux evaluation. The optional PyO3/maturin extension now computes flux divergence and the corresponding explicit stability bound in one Rust call over the whole grid. The Python reference remains the fallback and comparison implementation.

**Implemented and verified:**

- The native Windows extension builds and installs on CI; the dependency-free Rust core has 3 passing unit tests for flat grids, nodata holes, and invalid shapes/tensors.
- The Rust evaluator matches the Python reference on anisotropic cells, a non-diagonal diffusion tensor, and a nodata hole. The full run uses identical timesteps and mass balance; the 1024×1024 output difference was exactly 0.0.
- On the Windows Server 2025 / Python 3.12 CI runner, the latest synthetic 1024×1024, 10-step case took 1.048 s with Python and 0.205 s with Rust (5.1× faster), with exact output parity. The Rust-enabled suite reported 78 Python/Qt tests and 3 Rust core tests passing. These are controlled single-runner measurements, not a cross-machine or large-raster guarantee. See the [latest verification run](https://github.com/jiankarlocallejas-cpu/TerraSim/actions/runs/40090944062).

**Remaining work:**

- Profile the next hotspots and migrate only kernels that improve measured run time or peak memory.
- Reduce avoidable full-grid copies across the Python/Rust boundary and measure peak working set, not runtime alone.
- Keep the Python reference callable for parity checks; keep precision changes opt-in until their error is measured.
- Python tiled execution is now available under Stage 5; keep it memory-focused and verify any future native tile kernel against the Python reference.

**First-kernel exit gate:** passed for reference parity and measured runtime on the tested grid. The broader Rust migration remains in progress.

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

The Qt desktop workflow runs the Python reference model on a background worker, reports progress, supports checkpoint cancellation, estimates memory before raster loading, and exports final elevation and susceptibility GeoTIFFs. The Results page also saves and reopens a versioned run record with input metadata, coefficients, diagnostics, provenance, and output paths. An offscreen end-to-end check covers run, exports, run-record round-trip, and close-during-run cancellation.

The Rust-enabled Windows CI on the current implementation builds the extension, passes 3 Rust core tests and 78 Python/Qt tests, and verifies exact Python/Rust output parity on a 1024×1024, 10-step run (1.048 s Python, 0.205 s Rust on that runner). Python tiled execution also passes its synthetic full-grid parity and conservation gates, reducing measured local working-set growth by about 66% while taking about twice as long in that case. The application still loads complete raster inputs and retains output arrays in RAM: true windowed, disk-backed processing, scenario comparison, realistic large-raster profiles, and packaging remain future gates. The Scenarios page is still a placeholder. TerraSim is a terrain/sediment evolution model, not a fluid solver or CFD application.
