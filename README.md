# TerraSim Desktop

TerraSim is being rebuilt as a native Qt desktop application for GIS-integrated soil-erosion susceptibility and terrain simulation.

The active rebuild branch is `qt-desktop-rebuild`. The committed repository contains older web, API, and desktop experiments; this branch uses the Qt workbench as its application entry point.

## Run the desktop shell

Requirements: Python 3.8+.

```bash
python -m pip install -r requirements-desktop.txt
python terrasim.py
```

On Windows, `run.bat` launches the same desktop application. On macOS and Linux, use `bash run.sh`.

## Current desktop scope

- Native Qt project window with Overview, Input Data, Model Settings, Scenarios, and Results sections.
- Add and remove local raster, vector, and CSV input references.
- Save and reopen a `.terrasim.json` project.
- Relative α and β controls for exploratory sensitivity work, saved with the project.

The α and β controls are exploratory multipliers. The paper does not provide calibrated coefficient values or a conversion from soil erodibility tables to those coefficients. Soil-derived recommendations must retain their source and assumptions; they must not be presented as calibrated α/β values. The simulation and spatial rendering workflows remain to be rebuilt and connected to this interface.

## Scientific model reference

The supplied paper describes a weighted susceptibility index and a transport-and-diffusion model based on sediment flux divergence. Model implementation must preserve units, metric spatial resolution, parameter provenance, stability constraints, and explicit handling of missing calibration data.

## Repository notes

Older backend modules and historical web/API files are retained as reference while the desktop application is rebuilt. They are not launched by the Qt entry point.
