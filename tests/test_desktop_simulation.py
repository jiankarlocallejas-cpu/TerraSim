"""Offscreen Qt integration check for a full run and both GeoTIFF exports."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

pytest.importorskip("PyQt5")
from PyQt5.QtCore import QObject, QEventLoop, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QFileDialog

from desktop.main import TerraSimDesktop
from backend.services.run_manifest import load_run_manifest


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


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
        dataset.write(data.astype(np.float32), 1)


def test_qt_runs_in_background_and_exports_geotiffs(app, tmp_path, monkeypatch, caplog):
    caplog.set_level("WARNING", logger="rasterio._env")
    dem_path = tmp_path / "dem.tif"
    criterion_path = tmp_path / "criterion.tif"
    elevation = np.arange(64, dtype=np.float32).reshape(8, 8)
    criterion = np.linspace(0.0, 1.0, 64, dtype=np.float32).reshape(8, 8)
    _write_raster(dem_path, elevation)
    _write_raster(criterion_path, criterion)

    window = TerraSimDesktop()
    window._register_raster_path(str(dem_path))
    window._register_raster_path(str(criterion_path))
    window.layer_list.setCurrentRow(1)
    window.criterion_weight_control.setValue(1.0)
    window.total_time_spin.setValue(0.2)
    window.max_timestep_spin.setValue(0.1)
    window.alpha_base_spin.setValue(0.01)
    window.beta_base_spin.setValue(0.01)

    window._start_simulation()
    assert window._simulation_thread is not None
    assert window._simulation_thread.isRunning()

    event_loop = QEventLoop()
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(event_loop.quit)
    poll = QTimer()
    poll.setInterval(10)
    poll.timeout.connect(
        lambda: event_loop.quit() if window._simulation_thread is None else None
    )
    poll.start()
    timeout.start(10000)
    event_loop.exec_()
    poll.stop()
    timeout.stop()

    assert window._simulation_thread is None
    assert window._last_result is not None
    assert window._last_result.simulation.elapsed_time == pytest.approx(0.2)
    assert window._last_result.criterion_count == 1
    assert window.pages.currentIndex() == 4
    assert "Completed" in window.results_summary.text()
    assert not window.elevation_preview_image.pixmap().isNull()
    assert "Grid 8 × 8" in window.elevation_preview_caption.text()
    assert not window.susceptibility_preview_image.pixmap().isNull()

    elevation_output = tmp_path / "final-elevation.tif"
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        staticmethod(lambda *_args, **_kwargs: (str(elevation_output), "")),
    )
    window._export_elevation()
    with rasterio.open(elevation_output) as dataset:
        assert dataset.crs.to_string() == "EPSG:32650"
        assert dataset.transform == from_origin(500000, 1000, 30, 30)
        assert dataset.shape == elevation.shape
        assert np.all(np.isfinite(dataset.read(1)))

    susceptibility_output = tmp_path / "susceptibility.tif"
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        staticmethod(lambda *_args, **_kwargs: (str(susceptibility_output), "")),
    )
    window._export_susceptibility()
    with rasterio.open(susceptibility_output) as dataset:
        assert dataset.crs.to_string() == "EPSG:32650"
        assert dataset.transform == from_origin(500000, 1000, 30, 30)
        assert dataset.shape == criterion.shape
        assert dataset.read(1)[0, 0] == pytest.approx(0.0)
        assert dataset.read(1)[-1, -1] == pytest.approx(1.0)
    assert "BLOCKXSIZE can only be used with TILED=YES" not in caplog.text

    manifest_path = tmp_path / "run.terrasim-run.json"
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        staticmethod(lambda *_args, **_kwargs: (str(manifest_path), "")),
    )
    window._save_run_record()
    manifest = load_run_manifest(manifest_path)
    assert manifest["inputs"][0]["role"] == "elevation"
    assert manifest["inputs"][0]["metadata"]["crs"] == "EPSG:32650"
    assert manifest["model_settings"]["alpha"] == pytest.approx(0.01)
    assert manifest["model_settings"]["alpha_multiplier"] == pytest.approx(1.0)
    assert manifest["diagnostics"]["status"] == "completed"
    assert manifest["diagnostics"]["step_count"] > 0
    assert manifest["outputs"]["elevation"] == str(elevation_output)
    assert manifest["outputs"]["susceptibility"] == str(susceptibility_output)

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *_args, **_kwargs: (str(manifest_path), "")),
    )
    window._open_run_record()
    assert window._last_result is None
    assert "Saved run record" in window.results_summary.text()
    assert str(elevation_output) in window.results_summary.text()
    assert not window.export_elevation_button.isEnabled()
    assert not window.export_susceptibility_button.isEnabled()
    stored_pixmap = window.elevation_preview_image.pixmap()
    assert stored_pixmap is None or stored_pixmap.isNull()
    assert "Re-run or load exported GeoTIFFs" in window.elevation_preview_caption.text()

    window.close()
    app.processEvents()


def test_closing_during_run_cancels_and_waits_for_worker(app, tmp_path, monkeypatch):
    import desktop.main as desktop_main

    dem_path = tmp_path / "dem.tif"
    _write_raster(dem_path, np.zeros((4, 4), dtype=np.float32))
    cancelled = []

    class WaitingWorker(QObject):
        progress = pyqtSignal(int, float, float)
        succeeded = pyqtSignal(object)
        failed = pyqtSignal(str)
        cancelled = pyqtSignal()
        finished = pyqtSignal()

        def __init__(self, *_args, **_kwargs):
            super().__init__()

        @pyqtSlot()
        def run(self):
            while not QThread.currentThread().isInterruptionRequested():
                QThread.msleep(2)
            cancelled.append(True)
            self.cancelled.emit()
            self.finished.emit()

    monkeypatch.setattr(desktop_main, "SimulationWorker", WaitingWorker)
    window = TerraSimDesktop()
    window._register_raster_path(str(dem_path))
    window.show()
    window._start_simulation()
    assert window._simulation_thread is not None

    window.close()
    assert window._close_when_simulation_finishes
    assert window._simulation_thread.isRunning()

    event_loop = QEventLoop()
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(event_loop.quit)
    poll = QTimer()
    poll.setInterval(10)
    poll.timeout.connect(
        lambda: event_loop.quit()
        if window._simulation_thread is None and not window.isVisible()
        else None
    )
    poll.start()
    timeout.start(5000)
    event_loop.exec_()
    poll.stop()
    timeout.stop()

    assert cancelled == [True]
    assert window._simulation_thread is None
    assert not window.isVisible()
