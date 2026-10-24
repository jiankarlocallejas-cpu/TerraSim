"""Synthetic GeoTIFF tests for raster metadata and grid checks."""
import numpy as np
import pytest
import rasterio
from affine import Affine
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from backend.services.raster_inputs import (
    RasterGrid,
    RasterInputError,
    alignment_errors,
    load_geotiff,
    require_aligned,
)


def write_memory_raster(crs, transform, values=None, nodata=-9999.0):
    values = (
        np.array([[1.0, 2.0, 3.0], [4.0, nodata, 6.0]], dtype=np.float32)
        if values is None
        else np.asarray(values, dtype=np.float32)
    )
    memory_file = MemoryFile()
    dataset = memory_file.open(
        driver="GTiff",
        height=values.shape[0],
        width=values.shape[1],
        count=1,
        dtype="float32",
        crs=crs,
        transform=transform,
        nodata=nodata,
    )
    dataset.write(values, 1)
    dataset.close()
    return memory_file


def test_load_metric_geotiff_preserves_rectangular_pixels_and_nodata():
    memory_file = write_memory_raster(
        CRS.from_epsg(32650), from_origin(500000, 1000, 30, 10)
    )
    with memory_file:
        grid = load_geotiff(memory_file.name)

    assert grid.shape == (2, 3)
    assert grid.cell_size_x == pytest.approx(30.0)
    assert grid.cell_size_y == pytest.approx(10.0)
    assert grid.valid_mask.sum() == 5
    assert not grid.valid_mask[1, 1]
    assert grid.data[1, 1] == -9999.0
    assert grid.units == "metre"


@pytest.mark.parametrize(
    ("crs", "transform", "message"),
    [
        (CRS.from_epsg(4326), from_origin(0, 0, 0.001, 0.001), "projected"),
        (None, from_origin(0, 0, 30, 30), "coordinate reference system"),
        (
            CRS.from_epsg(32650),
            Affine(30, 0.25, 500000, 0.0, -30, 1000),
            "rotated or sheared",
        ),
    ],
)
def test_rejects_unusable_raster_geometry(crs, transform, message):
    memory_file = write_memory_raster(crs, transform)
    with memory_file, pytest.raises(RasterInputError, match=message):
        load_geotiff(memory_file.name)


def test_rejects_band_outside_raster():
    memory_file = write_memory_raster(
        CRS.from_epsg(32650), from_origin(500000, 1000, 30, 30)
    )
    with memory_file, pytest.raises(RasterInputError, match="contains 1 band"):
        load_geotiff(memory_file.name, band=2)


def test_alignment_reports_shape_crs_and_transform_mismatches():
    reference = RasterGrid(
        path="ref.tif",
        data=np.zeros((2, 3)),
        valid_mask=np.ones((2, 3), dtype=bool),
        crs="EPSG:32650",
        transform=(30.0, 0.0, 500000.0, 0.0, -30.0, 1000.0),
        cell_size_x=30.0,
        cell_size_y=30.0,
        units="metre",
        nodata=None,
    )
    shifted = RasterGrid(
        path="other.tif",
        data=np.zeros((1, 3)),
        valid_mask=np.ones((1, 3), dtype=bool),
        crs="EPSG:4326",
        transform=(10.0, 0.0, 0.0, 0.0, -10.0, 0.0),
        cell_size_x=10.0,
        cell_size_y=10.0,
        units="metre",
        nodata=None,
    )

    errors = alignment_errors(reference, shifted)

    assert len(errors) == 3
    with pytest.raises(RasterInputError, match="not aligned"):
        require_aligned(reference, shifted)


def test_aligned_grids_pass_exactly():
    values = np.zeros((2, 3))
    grid = RasterGrid(
        path="same.tif",
        data=values,
        valid_mask=np.ones(values.shape, dtype=bool),
        crs="EPSG:32650",
        transform=(30.0, 0.0, 500000.0, 0.0, -30.0, 1000.0),
        cell_size_x=30.0,
        cell_size_y=30.0,
        units="metre",
        nodata=None,
    )

    assert alignment_errors(grid, grid) == ()
    require_aligned(grid, grid)

