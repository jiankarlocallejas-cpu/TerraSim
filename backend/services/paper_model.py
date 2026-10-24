"""Paper-aligned terrain susceptibility and Exner reference model.

This module is deliberately a small-grid Python reference. It evolves terrain
from sediment-flux divergence; it does not solve water-flow or CFD equations.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Mapping, Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class ExnerStep:
    """One conservative, explicit terrain update."""

    elevation: np.ndarray
    valid_mask: np.ndarray
    timestep: float
    stable_timestep: float
    mass_before: float
    mass_after: float
    max_abs_elevation_change: float


@dataclass(frozen=True)
class ExnerSimulation:
    """Final terrain and run-level diagnostics; no timestep history is retained."""

    elevation: np.ndarray
    valid_mask: np.ndarray
    elapsed_time: float
    step_count: int
    min_stable_timestep: float
    mass_before: float
    mass_after: float
    max_abs_step_change: float
    cancelled: bool = False


def weighted_susceptibility_index(
    criteria: Mapping[str, np.ndarray],
    weights: Mapping[str, float],
    valid_mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Combine already-normalized [0, 1] criteria using explicit weights.

    Criteria are not rescaled or imputed here. A cell is nodata if any criterion
    is non-finite or if the optional validity mask excludes it.
    """
    if not criteria:
        raise ValueError("at least one susceptibility criterion is required")
    if set(criteria) != set(weights):
        raise ValueError("criteria and weight names must match exactly")

    total_weight = 0.0
    for name, weight in weights.items():
        if not math.isfinite(weight) or weight < 0.0:
            raise ValueError(f"weight for {name!r} must be finite and non-negative")
        total_weight += weight
    if not math.isclose(total_weight, 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("susceptibility weights must sum to 1")

    arrays = {name: np.asarray(value, dtype=np.float64) for name, value in criteria.items()}
    first = next(iter(arrays.values()))
    if first.ndim != 2 or first.size == 0:
        raise ValueError("criteria must be non-empty two-dimensional arrays")
    shape = first.shape
    valid = np.ones(shape, dtype=bool)
    if valid_mask is not None:
        supplied_mask = np.asarray(valid_mask, dtype=bool)
        if supplied_mask.shape != shape:
            raise ValueError("valid_mask shape must match the criteria")
        valid &= supplied_mask

    for name, values in arrays.items():
        if values.shape != shape:
            raise ValueError(f"criterion {name!r} has a different grid shape")
        finite = np.isfinite(values)
        if np.any(finite & ((values < 0.0) | (values > 1.0))):
            raise ValueError(f"criterion {name!r} must already be normalized to [0, 1]")
        valid &= finite

    index = np.full(shape, np.nan, dtype=np.float64)
    if np.any(valid):
        combined = np.zeros(shape, dtype=np.float64)
        for name, values in arrays.items():
            combined[valid] += values[valid] * weights[name]
        index[valid] = combined[valid]
    return index


class ExnerTerrainModel:
    """Small-grid reference for the paper's sediment-flux/Exner terrain update.

    Coordinates are projected linear units. Raster columns increase east and
    rows increase south. The diffusion tensor is dimensionless and symmetric
    positive-definite. Alpha and beta are the paper's transport coefficients;
    no soil-to-coefficient conversion or default calibration is assumed.

    The domain uses closed no-flux outer boundaries. Nodata cells are excluded
    and act as no-flux holes. Thus the sum of valid-cell elevations (volume up
    to a constant datum) is conserved by each update.
    """

    def __init__(
        self,
        cell_size_x: float,
        cell_size_y: float,
        alpha: float,
        beta: float,
        critical_slope_threshold: float,
        diffusion_tensor: np.ndarray = ((1.0, 0.0), (0.0, 1.0)),
        cfl: float = 0.25,
        nodata: Optional[float] = None,
    ) -> None:
        self.cell_size_x = self._positive_finite(cell_size_x, "cell_size_x")
        self.cell_size_y = self._positive_finite(cell_size_y, "cell_size_y")
        self.alpha = self._nonnegative_finite(alpha, "alpha")
        self.beta = self._nonnegative_finite(beta, "beta")
        self.critical_slope_threshold = self._nonnegative_finite(
            critical_slope_threshold, "critical_slope_threshold"
        )
        if not math.isfinite(cfl) or not (0.0 < cfl <= 1.0):
            raise ValueError("cfl must be finite and in (0, 1]")
        self.cfl = float(cfl)
        self.nodata = nodata

        tensor = np.asarray(diffusion_tensor, dtype=np.float64)
        if tensor.shape != (2, 2) or not np.all(np.isfinite(tensor)):
            raise ValueError("diffusion_tensor must be a finite 2x2 matrix")
        if not np.allclose(tensor, tensor.T, rtol=0.0, atol=1e-12):
            raise ValueError("diffusion_tensor must be symmetric")
        if float(np.min(np.linalg.eigvalsh(tensor))) <= 0.0:
            raise ValueError("diffusion_tensor must be positive-definite")
        self.diffusion_tensor = tensor.copy()

    @staticmethod
    def _positive_finite(value: float, name: str) -> float:
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be positive and finite")
        return float(value)

    @staticmethod
    def _nonnegative_finite(value: float, name: str) -> float:
        if not math.isfinite(value) or value < 0.0:
            raise ValueError(f"{name} must be finite and non-negative")
        return float(value)

    def _prepare_grid(
        self,
        elevation: np.ndarray,
        valid_mask: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        raw = np.asarray(elevation)
        if raw.ndim != 2 or raw.size == 0:
            raise ValueError("elevation must be a non-empty two-dimensional array")
        if not np.issubdtype(raw.dtype, np.number) or np.issubdtype(
            raw.dtype, np.complexfloating
        ):
            raise ValueError("elevation must contain real numeric values")

        grid = np.asarray(raw, dtype=np.float64).copy()
        valid = np.isfinite(grid)
        if self.nodata is not None and math.isfinite(self.nodata):
            valid &= grid != self.nodata
        if valid_mask is not None:
            supplied_mask = np.asarray(valid_mask, dtype=bool)
            if supplied_mask.shape != grid.shape:
                raise ValueError("valid_mask shape must match elevation")
            valid &= supplied_mask
        if not np.any(valid):
            raise ValueError("elevation grid contains no valid cells")
        return grid, valid

    @staticmethod
    def _gradient(
        grid: np.ndarray,
        valid: np.ndarray,
        axis: int,
        spacing: float,
        coordinate_sign: float,
    ) -> np.ndarray:
        """Differentiate using valid central or one-sided neighbors."""
        left = np.roll(grid, 1, axis=axis)
        right = np.roll(grid, -1, axis=axis)
        left_valid = np.roll(valid, 1, axis=axis)
        right_valid = np.roll(valid, -1, axis=axis)

        if axis == 0:
            left_valid[0, :] = False
            right_valid[-1, :] = False
        else:
            left_valid[:, 0] = False
            right_valid[:, -1] = False

        both = valid & left_valid & right_valid
        only_left = valid & left_valid & ~right_valid
        only_right = valid & right_valid & ~left_valid
        gradient = np.zeros(grid.shape, dtype=np.float64)
        gradient[both] = (right[both] - left[both]) / (2.0 * spacing)
        gradient[only_left] = (grid[only_left] - left[only_left]) / spacing
        gradient[only_right] = (right[only_right] - grid[only_right]) / spacing
        gradient *= coordinate_sign
        return gradient

    def _evaluate(
        self,
        grid: np.ndarray,
        valid: np.ndarray,
    ) -> Tuple[np.ndarray, float]:
        """Return flux divergence and a conservative explicit timestep bound."""
        dz_dx = self._gradient(grid, valid, axis=1, spacing=self.cell_size_x, coordinate_sign=1.0)
        # Raster rows point south, while the model's y coordinate points north.
        dz_dy = self._gradient(grid, valid, axis=0, spacing=self.cell_size_y, coordinate_sign=-1.0)

        tensor_grad_x = (
            self.diffusion_tensor[0, 0] * dz_dx
            + self.diffusion_tensor[0, 1] * dz_dy
        )
        tensor_grad_y = (
            self.diffusion_tensor[1, 0] * dz_dx
            + self.diffusion_tensor[1, 1] * dz_dy
        )
        slope_measure = np.maximum(dz_dx * tensor_grad_x + dz_dy * tensor_grad_y, 0.0)
        active = slope_measure > self.critical_slope_threshold
        excess = np.maximum(slope_measure - self.critical_slope_threshold, 0.0)
        capacity = self.alpha * excess + self.beta

        flux_x = -capacity * tensor_grad_x
        flux_y = -capacity * tensor_grad_y
        flux_x[~valid] = 0.0
        flux_y[~valid] = 0.0

        rows, cols = grid.shape
        face_x = np.zeros((rows, cols + 1), dtype=np.float64)
        face_y = np.zeros((rows + 1, cols), dtype=np.float64)
        if cols > 1:
            open_x = valid[:, :-1] & valid[:, 1:]
            mean_x = 0.5 * (flux_x[:, :-1] + flux_x[:, 1:])
            face_x[:, 1:-1] = np.where(open_x, mean_x, 0.0)
        if rows > 1:
            open_y = valid[:-1, :] & valid[1:, :]
            mean_y = 0.5 * (flux_y[:-1, :] + flux_y[1:, :])
            face_y[1:-1, :] = np.where(open_y, mean_y, 0.0)

        divergence = (
            np.diff(face_x, axis=1) / self.cell_size_x
            + np.diff(face_y, axis=0) / self.cell_size_y
        )
        divergence[~valid] = 0.0

        active_float = active.astype(np.float64)
        jac_xx = capacity * self.diffusion_tensor[0, 0] + (
            2.0 * self.alpha * active_float * tensor_grad_x**2
        )
        jac_yy = capacity * self.diffusion_tensor[1, 1] + (
            2.0 * self.alpha * active_float * tensor_grad_y**2
        )
        jac_xy = capacity * self.diffusion_tensor[0, 1] + (
            2.0 * self.alpha * active_float * tensor_grad_x * tensor_grad_y
        )
        if np.any(valid):
            rate_bound = 2.0 * (
                float(np.max(jac_xx[valid])) / self.cell_size_x**2
                + float(np.max(jac_yy[valid])) / self.cell_size_y**2
                + float(np.max(np.abs(jac_xy[valid]))
                        / (self.cell_size_x * self.cell_size_y))
            )
        else:
            rate_bound = 0.0
        stable_timestep = self.cfl / rate_bound if rate_bound > 0.0 else math.inf

        if not np.all(np.isfinite(divergence[valid])):
            raise FloatingPointError("non-finite sediment-flux divergence")
        return divergence, stable_timestep

    @staticmethod
    def _mass(grid: np.ndarray, valid: np.ndarray, cell_area: float) -> float:
        return float(np.sum(grid[valid], dtype=np.float64) * cell_area)

    def stable_timestep(
        self,
        elevation: np.ndarray,
        valid_mask: Optional[np.ndarray] = None,
    ) -> float:
        """Return a conservative local explicit timestep bound for this terrain."""
        grid, valid = self._prepare_grid(elevation, valid_mask)
        _, stable_timestep = self._evaluate(grid, valid)
        return stable_timestep

    def step(
        self,
        elevation: np.ndarray,
        timestep: float,
        valid_mask: Optional[np.ndarray] = None,
    ) -> ExnerStep:
        """Apply one explicit step, rejecting a timestep above its stability bound."""
        if not math.isfinite(timestep) or timestep <= 0.0:
            raise ValueError("timestep must be positive and finite")
        grid, valid = self._prepare_grid(elevation, valid_mask)
        divergence, stable_timestep = self._evaluate(grid, valid)
        if timestep > stable_timestep * (1.0 + 1e-12):
            raise ValueError(
                f"timestep {timestep:g} exceeds conservative stability limit "
                f"{stable_timestep:g}"
            )

        updated = grid.copy()
        updated[valid] -= timestep * divergence[valid]
        if not np.all(np.isfinite(updated[valid])):
            raise FloatingPointError("terrain update produced non-finite elevations")
        cell_area = self.cell_size_x * self.cell_size_y
        mass_before = self._mass(grid, valid, cell_area)
        mass_after = self._mass(updated, valid, cell_area)
        max_change = float(np.max(np.abs(updated[valid] - grid[valid])))
        return ExnerStep(
            elevation=updated,
            valid_mask=valid,
            timestep=float(timestep),
            stable_timestep=stable_timestep,
            mass_before=mass_before,
            mass_after=mass_after,
            max_abs_elevation_change=max_change,
        )

    def simulate(
        self,
        elevation: np.ndarray,
        total_time: float,
        max_timestep: float,
        valid_mask: Optional[np.ndarray] = None,
        progress: Optional[Callable[[int, float, float], None]] = None,
        cancel_requested: Optional[Callable[[], bool]] = None,
        max_steps: int = 1_000_000,
    ) -> ExnerSimulation:
        """Evolve terrain without retaining intermediate grids in memory.

        Each explicit substep is bounded by both max_timestep and the current
        terrain's conservative CFL estimate. The progress callback receives
        (completed_steps, elapsed_time, actual_step_size).
        """
        if not math.isfinite(total_time) or total_time <= 0.0:
            raise ValueError("total_time must be positive and finite")
        if not math.isfinite(max_timestep) or max_timestep <= 0.0:
            raise ValueError("max_timestep must be positive and finite")
        if not isinstance(max_steps, int) or max_steps <= 0:
            raise ValueError("max_steps must be a positive integer")

        grid, valid = self._prepare_grid(elevation, valid_mask)
        cell_area = self.cell_size_x * self.cell_size_y
        mass_before = self._mass(grid, valid, cell_area)
        elapsed = 0.0
        step_count = 0
        was_cancelled = False
        min_stable_timestep = math.inf
        max_abs_step_change = 0.0

        while elapsed < total_time:
            if cancel_requested is not None and cancel_requested():
                was_cancelled = True
                break
            if step_count >= max_steps:
                raise RuntimeError("simulation exceeded max_steps before reaching total_time")
            divergence, stable_timestep = self._evaluate(grid, valid)
            step_size = min(max_timestep, stable_timestep, total_time - elapsed)
            if not math.isfinite(step_size) or step_size <= 0.0:
                raise FloatingPointError("no positive finite timestep is available")
            next_grid = grid.copy()
            next_grid[valid] -= step_size * divergence[valid]
            if not np.all(np.isfinite(next_grid[valid])):
                raise FloatingPointError("terrain update produced non-finite elevations")

            max_abs_step_change = max(
                max_abs_step_change,
                float(np.max(np.abs(next_grid[valid] - grid[valid]))),
            )
            grid = next_grid
            step_count += 1
            min_stable_timestep = min(min_stable_timestep, stable_timestep)
            if step_size == total_time - elapsed:
                elapsed = total_time
            else:
                next_elapsed = elapsed + step_size
                if next_elapsed <= elapsed:
                    raise FloatingPointError("timestep is too small to advance simulation time")
                elapsed = next_elapsed
            if progress is not None:
                progress(step_count, elapsed, step_size)

        return ExnerSimulation(
            elevation=grid,
            valid_mask=valid,
            elapsed_time=elapsed,
            step_count=step_count,
            min_stable_timestep=min_stable_timestep,
            mass_before=mass_before,
            mass_after=self._mass(grid, valid, cell_area),
            max_abs_step_change=max_abs_step_change,
            cancelled=was_cancelled,
        )


