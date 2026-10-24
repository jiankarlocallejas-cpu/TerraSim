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
- Assign one DEM and criterion rasters, and flag mismatched CRS, dimensions, or pixel transforms.
- Save and reopen raster roles, input metadata, and model controls in a `.terrasim.json` project.

## Model status

The Python reference services include D-infinity terrain routing and the paper-aligned weighted susceptibility and Exner terrain-update equations. D-infinity routes flow direction and contributing area; it is not a water-flow solver. The Exner reference uses closed no-flux boundaries, masks nodata, checks explicit timestep stability, and conserves valid terrain volume.

The numerical solver is not yet connected to Qt's Run workflow, and output raster export and tiled/out-of-core simulation remain to be implemented. The relative `α` and `β` controls are exploratory multipliers; coefficient calibration and a defensible conversion from soil/rainfall data are not supplied by the paper. Users must provide parameter values and provenance before interpreting a run scientifically.

TerraSim is not CFD-capable. A water-flow solver would require a separate governing-equation and validation phase.

## Repository notes

Older backend modules and historical web/API files are retained as references while the desktop application is rebuilt. They are not launched by the Qt entry point. The implementation sequence and verification gates are tracked in [the rebuild roadmap](docs/rust-compute-roadmap.md).
