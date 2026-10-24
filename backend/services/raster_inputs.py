"""GeoTIFF reading and grid validation for TerraSim's raster models."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np


class RasterInputError(ValueError):
    """Input raster cannot safely be used by the terrain model."""


@dataclass(frozen=True)
class RasterMetadata:
    """Lightweight GeoTIFF metadata for preflight checks without reading pixels."""

    path: str
    width: int
    height: int
    crs: str
    transform: Tuple[float, float, float, float, float, float]
    cell_size_x: float
    cell_size_y: float
    units: str
    nodata: Optional[float]
    band: int
    dtype: str

    @property
    def shape(self) -> Tuple[int, int]:
        return self.height, self.width


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


def _get_rasterio():
    try:
        import rasterio
    except ImportError as exc:
        raise RasterInputError(
            "GeoTIFF support requires Rasterio; install the desktop GIS requirements."
        ) from exc
    return rasterio


def _resolve_path(path: str) -> str:
    value = str(path)
    if value.startswith("/vsi"):
        return value
    return str(Path(value).expanduser().resolve())


def _inspect_dataset(dataset, source_path: str, band: int) -> RasterMetadata:
    if not isinstance(band, int) or band < 1:
        raise RasterInputError("band must be a positive integer")
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

    return RasterMetadata(
        path=source_path,
        width=int(dataset.width),
        height=int(dataset.height),
        crs=dataset.crs.to_string(),
        transform=tuple(float(value) for value in transform)[:6],
        cell_size_x=cell_size_x,
        cell_size_y=cell_size_y,
        units=units,
        nodata=float(dataset.nodata) if dataset.nodata is not None else None,
        band=band,
        dtype=str(dataset.dtypes[band - 1]),
    )


def inspect_geotiff(path: str, band: int = 1) -> RasterMetadata:
    """Validate raster geometry and return metadata without allocating its grid."""
    rasterio = _get_rasterio()
    source_path = _resolve_path(path)
    try:
        with rasterio.open(source_path) as dataset:
            return _inspect_dataset(dataset, source_path, band)
    except RasterInputError:
        raise
    except rasterio.errors.RasterioError as exc:
        raise RasterInputError(f"could not inspect raster {source_path}: {exc}") from exc


def load_geotiff(path: str, band: int = 1) -> RasterGrid:
    """Read one metric, north-up GeoTIFF band and preserve its nodata mask."""
    rasterio = _get_rasterio()
    source_path = _resolve_path(path)
    try:
        with rasterio.open(source_path) as dataset:
            metadata = _inspect_dataset(dataset, source_path, band)
            masked = dataset.read(band, masked=True)
            data = np.asarray(masked.data)
            if not np.issubdtype(data.dtype, np.number) or np.issubdtype(
                data.dtype, np.complexfloating
            ):
                raise RasterInputError("raster band must contain real numeric values")
            valid = ~np.ma.getmaskarray(masked)
            valid &= np.isfinite(data)
            return RasterGrid(
                path=metadata.path,
                data=data,
                valid_mask=valid,
                crs=metadata.crs,
                transform=metadata.transform,
                cell_size_x=metadata.cell_size_x,
                cell_size_y=metadata.cell_size_y,
                units=metadata.units,
                nodata=metadata.nodata,
            )
    except RasterInputError:
        raise
    except rasterio.errors.RasterioError as exc:
        raise RasterInputError(f"could not read raster {source_path}: {exc}") from exc


def alignment_errors(
    reference: Union[RasterGrid, RasterMetadata],
    candidate: Union[RasterGrid, RasterMetadata],
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


def require_aligned(
    reference: Union[RasterGrid, RasterMetadata],
    candidate: Union[RasterGrid, RasterMetadata],
) -> None:
    """Raise a useful error when a raster cannot be combined cell by cell."""
    issues = alignment_errors(reference, candidate)
    if issues:
        details = "; ".join(issues)
        raise RasterInputError(f"raster is not aligned with the reference grid: {details}")



def save_geotiff(
    reference_path: str,
    output_path: str,
    elevation: np.ndarray,
    valid_mask: np.ndarray,
) -> str:
    """Write one float64 result band using a reference grid's spatial metadata.

    Existing files are never overwritten. Invalid cells are written as the
    reference nodata value, or NaN when the reference has no nodata value.
    """
    rasterio = _get_rasterio()
    reference = _resolve_path(reference_path)
    destination = Path(output_path).expanduser().resolve()
    if destination.exists():
        raise FileExistsError(f"output already exists: {destination}")
    if not destination.parent.exists():
        raise RasterInputError(f"output directory does not exist: {destination.parent}")

    values = np.asarray(elevation, dtype=np.float64)
    mask = np.asarray(valid_mask, dtype=bool)
    if values.ndim != 2 or values.shape != mask.shape:
        raise RasterInputError("elevation and valid_mask must be matching 2D arrays")
    if not np.all(np.isfinite(values[mask])):
        raise RasterInputError("valid result cells must contain finite elevations")

    try:
        with rasterio.open(reference) as source:
            if values.shape != (source.height, source.width):
                raise RasterInputError("result grid shape does not match the reference raster")
            nodata = source.nodata if source.nodata is not None else float("nan")
            profile = source.profile.copy()
            profile.update(
                count=1,
                dtype="float64",
                nodata=nodata,
                compress="deflate",
            )
            if not profile.get("tiled", False):
                profile.pop("blockxsize", None)
                profile.pop("blockysize", None)
            if np.any(~mask):
                output = values.copy()
                output[~mask] = nodata
            else:
                output = values
        with rasterio.open(str(destination), "w", **profile) as target:
            target.write(output, 1)
    except RasterInputError:
        raise
    except rasterio.errors.RasterioError as exc:
        raise RasterInputError(f"could not write result raster {destination}: {exc}") from exc
    return str(destination)
