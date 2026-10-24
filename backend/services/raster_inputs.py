"""GeoTIFF reading and grid validation for TerraSim's raster models."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import numpy as np


class RasterInputError(ValueError):
    """Input raster cannot safely be used by the terrain model."""


@dataclass(frozen=True)
class RasterGrid:
    """A raster band and the spatial metadata required for model calculations."""

    path: str
    data: np.ndarray
    valid_mask: np.ndarray
    crs: str
    transform: Tuple[float, float, float, float, float, float]
    cell_size_x: float
    cell_size_y: float
    units: str
    nodata: Optional[float]

    @property
    def shape(self) -> Tuple[int, int]:
        return self.data.shape


def load_geotiff(path: str, band: int = 1) -> RasterGrid:
    """Read one metric, north-up GeoTIFF band and preserve its nodata mask."""
    try:
        import rasterio
    except ImportError as exc:
        raise RasterInputError(
            "GeoTIFF support requires Rasterio; install the desktop GIS requirements."
        ) from exc

    if not isinstance(band, int) or band < 1:
        raise RasterInputError("band must be a positive integer")
    source_path = path if str(path).startswith("/vsi") else str(Path(path).expanduser().resolve())
    try:
        with rasterio.open(source_path) as dataset:
            if band > dataset.count:
                raise RasterInputError(
                    f"requested band {band}, but raster contains {dataset.count} band(s)"
                )
            if dataset.crs is None:
                raise RasterInputError("raster has no coordinate reference system")
            if not dataset.crs.is_projected:
                raise RasterInputError(
                    "raster CRS must be projected; angular coordinates cannot be used for metric gradients"
                )
            units = str(dataset.crs.linear_units or "").strip().lower()
            if units not in {"metre", "meter", "metres", "meters"}:
                raise RasterInputError(
                    f"raster CRS uses {units or 'unknown units'}; reproject to a metric CRS"
                )

            transform = dataset.transform
            if not np.isclose(transform.b, 0.0, rtol=0.0, atol=1e-12) or not np.isclose(
                transform.d, 0.0, rtol=0.0, atol=1e-12
            ):
                raise RasterInputError(
                    "rotated or sheared rasters must be reprojected to a north-up grid"
                )
            cell_size_x = abs(float(transform.a))
            cell_size_y = abs(float(transform.e))
            if (
                not np.isfinite(cell_size_x)
                or not np.isfinite(cell_size_y)
                or cell_size_x <= 0.0
                or cell_size_y <= 0.0
            ):
                raise RasterInputError("raster pixel dimensions must be positive and finite")

            masked = dataset.read(band, masked=True)
            data = np.asarray(masked.data)
            valid = ~np.ma.getmaskarray(masked)
            if not np.issubdtype(data.dtype, np.number) or np.issubdtype(
                data.dtype, np.complexfloating
            ):
                raise RasterInputError("raster band must contain real numeric values")
            valid &= np.isfinite(data)
            affine = tuple(float(value) for value in transform)[:6]
            nodata = dataset.nodata
            return RasterGrid(
                path=source_path,
                data=data,
                valid_mask=valid,
                crs=dataset.crs.to_string(),
                transform=affine,
                cell_size_x=cell_size_x,
                cell_size_y=cell_size_y,
                units=units,
                nodata=float(nodata) if nodata is not None else None,
            )
    except RasterInputError:
        raise
    except rasterio.errors.RasterioError as exc:
        raise RasterInputError(f"could not read raster {source_path}: {exc}") from exc


def alignment_errors(
    reference: RasterGrid,
    candidate: RasterGrid,
    transform_tolerance: float = 1e-8,
) -> Tuple[str, ...]:
    """Return all grid mismatches that prevent cell-by-cell raster operations."""
    issues = []
    if reference.shape != candidate.shape:
        issues.append(f"shape differs: {candidate.shape} vs {reference.shape}")
    if reference.crs != candidate.crs:
        issues.append(f"CRS differs: {candidate.crs} vs {reference.crs}")
    if not np.allclose(
        reference.transform,
        candidate.transform,
        rtol=0.0,
        atol=transform_tolerance,
    ):
        issues.append("affine transform differs")
    return tuple(issues)


def require_aligned(reference: RasterGrid, candidate: RasterGrid) -> None:
    """Raise a useful error when a raster cannot be combined cell by cell."""
    issues = alignment_errors(reference, candidate)
    if issues:
        details = "; ".join(issues)
        raise RasterInputError(f"raster is not aligned with the reference grid: {details}")

