"""Offscreen smoke tests for the Qt raster input page."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

pytest.importorskip("PyQt5")
from PyQt5.QtWidgets import QApplication, QFileDialog

from desktop.main import TerraSimDesktop


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


def _write_raster(path, x_origin):
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=5,
        width=5,
        count=1,
        dtype="float32",
        crs="EPSG:32650",
        transform=from_origin(x_origin, 1000, 30, 30),
        nodata=-9999.0,
    ) as dataset:
        dataset.write(np.arange(25, dtype=np.float32).reshape(5, 5), 1)


def test_input_page_inspects_alignment_and_project_round_trip(app, tmp_path, monkeypatch):
    dem_path = tmp_path / "dem.tif"
    factor_path = tmp_path / "factor.tif"
    _write_raster(dem_path, 500000)
    _write_raster(factor_path, 500030)

    window = TerraSimDesktop()
    window._register_raster_path(str(dem_path))
    window._register_raster_path(str(factor_path))

    assert window.layers[0]["role"] == "elevation"
    assert window.layers[1]["role"] == "criterion"
    assert "need matching" in window.data_hint.text()
    assert "not aligned" in window.layer_list.item(1).text()

    window.layer_list.setCurrentRow(1)
    window._set_layer_role("elevation")
    window.alpha_control.set_multiplier(1.4)
    project_path = tmp_path / "sample.terrasim.json"
    window.project_path = project_path
    window._save_project()
    window.close()

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *_args, **_kwargs: (str(project_path), "")),
    )
    reopened = TerraSimDesktop()
    reopened._open_project()

    assert reopened.layers[1]["role"] == "elevation"
    assert reopened.layers[0]["role"] == "criterion"
    assert reopened.alpha_control.multiplier == pytest.approx(1.4)
    assert reopened.layers[1]["metadata"]["crs"] == "EPSG:32650"
    reopened.close()
    app.processEvents()

