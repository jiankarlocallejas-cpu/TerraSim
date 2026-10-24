"""Small, downsampled Qt images for rapid inspection of raster results."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PyQt5.QtGui import QImage


@dataclass(frozen=True)
class RasterPreview:
    image: QImage
    source_width: int
    source_height: int
    minimum: float
    maximum: float


_PALETTES = {
    "terrain": (
        (35, 94, 68),
        (126, 144, 83),
        (193, 164, 114),
        (242, 237, 218),
    ),
    "susceptibility": (
        (42, 112, 112),
        (121, 165, 106),
        (224, 177, 77),
        (174, 70, 57),
    ),
}


def render_raster_preview(
    values: np.ndarray,
    valid_mask: np.ndarray | None = None,
    *,
    palette: str = "terrain",
    max_width: int = 512,
    max_height: int = 384,
) -> RasterPreview:
    """Create a bounded RGB image with nearest-neighbor sampling.

    The preview is a visual aid, not an analysis raster. It preserves the grid's
    aspect ratio, masks invalid samples, and reports the full-grid value range.
    """
    grid = np.asarray(values)
    if grid.ndim != 2 or grid.size == 0:
        raise ValueError("preview values must be a non-empty two-dimensional array")
    if max_width <= 0 or max_height <= 0:
        raise ValueError("preview bounds must be positive")
    try:
        stops = np.asarray(_PALETTES[palette], dtype=np.float64)
    except KeyError as exc:
        raise ValueError(f"unknown raster preview palette: {palette}") from exc

    data = np.asarray(grid, dtype=np.float64)
    valid = np.isfinite(data)
    if valid_mask is not None:
        supplied = np.asarray(valid_mask, dtype=bool)
        if supplied.shape != data.shape:
            raise ValueError("preview valid_mask shape must match raster values")
        valid &= supplied
    if not np.any(valid):
        raise ValueError("preview raster contains no valid cells")

    minimum = float(np.min(data, where=valid, initial=np.inf))
    maximum = float(np.max(data, where=valid, initial=-np.inf))
    source_height, source_width = data.shape
    scale = min(1.0, max_width / source_width, max_height / source_height)
    preview_width = max(1, int(round(source_width * scale)))
    preview_height = max(1, int(round(source_height * scale)))
    row_indices = np.linspace(0, source_height - 1, preview_height).astype(np.intp)
    column_indices = np.linspace(0, source_width - 1, preview_width).astype(np.intp)
    sample = data[np.ix_(row_indices, column_indices)]
    sample_valid = valid[np.ix_(row_indices, column_indices)]

    if maximum > minimum:
        normalized = np.clip((sample - minimum) / (maximum - minimum), 0.0, 1.0)
    else:
        normalized = np.full(sample.shape, 0.5, dtype=np.float64)
    positions = normalized * (len(stops) - 1)
    lower = np.minimum(positions.astype(np.intp), len(stops) - 2)
    fraction = (positions - lower)[..., np.newaxis]
    rgb = stops[lower] * (1.0 - fraction) + stops[lower + 1] * fraction
    rgb = np.rint(rgb).astype(np.uint8)
    rgb[~sample_valid] = (210, 215, 219)
    rgb = np.ascontiguousarray(rgb)

    image = QImage(
        rgb.data,
        preview_width,
        preview_height,
        rgb.strides[0],
        QImage.Format_RGB888,
    ).copy()
    return RasterPreview(
        image=image,
        source_width=source_width,
        source_height=source_height,
        minimum=minimum,
        maximum=maximum,
    )
