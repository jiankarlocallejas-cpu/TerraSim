# TerraSim Desktop

TerraSim is being rebuilt as a native Qt desktop application for GIS-integrated soil-erosion susceptibility and terrain simulation.

The active rebuild branch is `qt-desktop-rebuild`. The committed repository contains older web, API, and desktop experiments; this branch launches the Qt workbench.

## Run

Requirements: Python 3.9 or newer.

```bash
python -m pip install -r requirements-desktop.txt
python terrasim.py
```

On Windows, `run.bat` launches the same application. On macOS and Linux, use `bash run.sh`.

## Current desktop features

- Native Qt project window with Overview, Input Data, Model Settings, Scenarios, and Results sections.
- Inspect GeoTIFF metadata without loading raster pixels; require a projected metre-based CRS and a north-up grid.
- Assign one DEM and criterion rasters, set explicit MCE weights, and flag mismatched CRS, dimensions, or pixel transforms.
- Save and reopen raster roles, input metadata, and model controls in a `.terrasim.json` project.
- Run MCE susceptibility and the paper-aligned Exner terrain update on a background Qt worker with progress, cancellation, and an approximate memory preflight.
- Review timestep, elevation-volume, maximum-step-change, and susceptibility summaries; export final elevation and susceptibility GeoTIFFs with source-grid metadata.
- Preview bounded spatial views of the DEM and saved run outputs without retaining rendered full-size copies.
- Save and reopen a `.terrasim-run.json` record with raster metadata, exact model settings, diagnostics, coefficient provenance, and exported output paths.
- Select Automatic, Full grid, or tiled 256/512/1024 processing. Tiling bounds stencil workspace but currently keeps the full raster inputs and outputs in memory.

## Model status

The Python reference services include D-infinity terrain routing and a weighted susceptibility overlay plus conservative Exner terrain update. D-infinity estimates flow direction and contributing area; it is not a water-flow solver. The Exner update applies sediment-flux divergence with closed no-flux boundaries, nodata masks, and explicit stability limits. The Qt Run workflow loads aligned rasters, computes the selected model, shows run diagnostics, and exports GeoTIFF results.

The Python reference remains the correctness path. An optional Rust extension evaluates sediment-flux divergence and the explicit timestep bound; install it with `python -m pip install ./rust/terrasim_compute` after installing the Rust toolchain and a C++ build toolchain. Without the extension, TerraSim uses the Python reference path. Rust-enabled Windows CI passes 78 Python/Qt tests and 3 Rust core tests; its 1024×1024, 10-step case matched the Python output exactly and ran in 0.205 s versus 1.048 s for Python (5.1× on that runner; [workflow](https://github.com/jiankarlocallejas-cpu/TerraSim/actions/runs/40090944062)).

The tiled Python path matches the full-grid result on tested synthetic cases and lowers stencil workspace memory. In one local Windows/Python 3.12 comparison of a 1024×1024, 10-step case, working-set growth was about 180–181 MiB for full grid and 61.2 MiB for 512×512 tiles; tile execution took 6.48 s versus 3.06 s for full grid. This is one machine and workload: tiling trades runtime for memory. The current tiled path still loads the full DEM, criteria, susceptibility result, and final elevation in memory; it is not out-of-core. Memory preflight is an estimate, not an operating-system guarantee. Spatial previews and saved run records are available; scenario comparison, windowed disk-backed processing, and desktop packaging remain open. Saved run records store paths and metadata rather than raster arrays, so reopening restores the report without loading prior raster data. The relative `α` and `β` controls remain exploratory; the paper does not provide a validated conversion from soil or rainfall inputs to those coefficients. Record their provenance before scientific interpretation.

TerraSim is not CFD-capable. A water-flow solver would need a separate governing-equation, boundary-condition, and validation phase.

## Repository notes

Older backend modules and historical web/API files are retained as references while the desktop application is rebuilt. They are not launched by the Qt entry point. The implementation sequence and verification gates are tracked in [the rebuild roadmap](docs/rust-compute-roadmap.md).
