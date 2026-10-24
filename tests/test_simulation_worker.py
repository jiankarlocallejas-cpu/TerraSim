"""Worker tests for end-to-end raster-to-model execution."""
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

pytest.importorskip("PyQt5")
from PyQt5.QtWidgets import QApplication

from desktop.simulation_worker import SimulationWorker


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def _write_raster(path, data):
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype="float32",
        crs="EPSG:32650",
        transform=from_origin(500000, 1000, 30, 30),
        nodata=-9999.0,
    ) as dataset:
        dataset.write(np.asarray(data, dtype=np.float32), 1)


def _settings():
    return {
        "alpha": 0.0,
        "beta": 0.0,
        "critical_slope_threshold": 0.0,
        "d_xx": 1.0,
        "d_xy": 0.0,
        "d_yy": 1.0,
        "cfl": 0.25,
        "total_time": 1.0,
        "max_timestep": 0.25,
    }


def test_worker_loads_aligned_rasters_builds_mce_and_runs_dem(app, tmp_path):
    dem_path = tmp_path / "dem.tif"
    factor_path = tmp_path / "factor.tif"
    _write_raster(dem_path, np.arange(25).reshape(5, 5))
    _write_raster(factor_path, np.linspace(0.0, 1.0, 25).reshape(5, 5))
    dem_layer = {"path": str(dem_path), "band": 1}
    criteria = [{"path": str(factor_path), "band": 1, "weight": 1.0}]
    worker = SimulationWorker(dem_layer, criteria, _settings(), memory_budget_bytes=1_000_000)
    succeeded = []
    failed = []
    worker.succeeded.connect(succeeded.append)
    worker.failed.connect(failed.append)

    worker.run()

    assert not failed
    assert len(succeeded) == 1
    result = succeeded[0]
    assert result.criterion_count == 1
    assert result.susceptibility_index[0, 0] == pytest.approx(0.0)
    assert result.susceptibility_index[-1, -1] == pytest.approx(1.0)
    assert np.array_equal(result.simulation.elevation, np.arange(25).reshape(5, 5))


def test_worker_stops_before_pixel_load_when_memory_budget_is_too_small(
    app, tmp_path
):
    dem_path = tmp_path / "dem.tif"
    _write_raster(dem_path, np.zeros((5, 5)))
    worker = SimulationWorker(
        {"path": str(dem_path), "band": 1},
        [],
        _settings(),
        memory_budget_bytes=1,
    )
    failed = []
    worker.failed.connect(failed.append)

    worker.run()

    assert len(failed) == 1
    assert "above the selected" in failed[0]

