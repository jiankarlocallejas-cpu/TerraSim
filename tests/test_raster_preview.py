"""Checks for bounded, aspect-preserving raster result previews."""
import numpy as np
import pytest

pytest.importorskip("PyQt5")

from desktop.raster_preview import render_raster_preview


def test_preview_is_bounded_and_reports_full_grid_range():
    values = np.arange(200 * 400, dtype=np.float32).reshape(200, 400)

    preview = render_raster_preview(values, max_width=120, max_height=90)

    assert preview.image.width() == 120
    assert preview.image.height() == 60
    assert preview.source_width == 400
    assert preview.source_height == 200
    assert preview.minimum == 0.0
    assert preview.maximum == float(values[-1, -1])


def test_preview_colors_invalid_cells_and_handles_flat_rasters():
    values = np.full((3, 4), 7.0)
    valid = np.ones(values.shape, dtype=bool)
    valid[0, 0] = False

    preview = render_raster_preview(values, valid, palette="susceptibility")

    assert preview.minimum == preview.maximum == 7.0
    assert preview.image.pixelColor(0, 0).getRgb()[:3] == (210, 215, 219)
    assert preview.image.pixelColor(1, 1).getRgb()[:3] != (210, 215, 219)


def test_preview_rejects_mismatched_masks_and_unknown_palettes():
    with pytest.raises(ValueError, match="shape must match"):
        render_raster_preview(np.ones((2, 2)), np.ones((3, 3), dtype=bool))
    with pytest.raises(ValueError, match="unknown raster preview palette"):
        render_raster_preview(np.ones((2, 2)), palette="unknown")
