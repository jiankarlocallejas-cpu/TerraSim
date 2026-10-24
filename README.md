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

## Model status

The Python reference services include D-infinity terrain routing and a weighted susceptibility overlay plus conservative Exner terrain update. D-infinity estimates flow direction and contributing area; it is not a water-flow solver. The Exner update applies sediment-flux divergence with closed no-flux boundaries, nodata masks, and explicit stability limits. The Qt Run workflow loads aligned rasters, computes the selected model, shows run diagnostics, and exports GeoTIFF results.

The solver remains a small-grid Python reference. Tiled/out-of-core processing, reopening saved runs, run manifests, map previews, and Rust acceleration are not implemented yet. Memory preflight is an estimate, not an operating-system guarantee. The relative `α` and `β` controls are exploratory multipliers; the paper does not provide a validated conversion from soil or rainfall inputs to those coefficients. Users must enter values and record their provenance before scientific interpretation.

TerraSim is not CFD-capable. A water-flow solver would need a separate governing-equation, boundary-condition, and validation phase.

## Repository notes

Older backend modules and historical web/API files are retained as references while the desktop application is rebuilt. They are not launched by the Qt entry point. The implementation sequence and verification gates are tracked in [the rebuild roadmap](docs/rust-compute-roadmap.md).
