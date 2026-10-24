"""Background GeoTIFF loading and paper-model execution for the Qt app."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from backend.services.paper_model import (
    ExnerSimulation,
    ExnerTerrainModel,
    estimate_reference_memory_bytes,
    weighted_susceptibility_index,
)
from backend.services.raster_inputs import (
    inspect_geotiff,
    load_geotiff,
    require_aligned,
)


@dataclass(frozen=True)
class DesktopSimulationResult:
    dem_path: str
    simulation: ExnerSimulation
    susceptibility_index: Optional[np.ndarray]
    estimated_memory_bytes: int
    criterion_count: int
    model_settings: dict[str, float]
    input_layers: list[dict[str, Any]]


class SimulationWorker(QObject):
    """Load inputs and run outside the GUI thread."""

    progress = pyqtSignal(int, float, float)
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()
    finished = pyqtSignal()

    def __init__(
        self,
        dem_layer: dict[str, Any],
        criterion_layers: list[dict[str, Any]],
        model_settings: dict[str, float],
        memory_budget_bytes: int,
    ) -> None:
        super().__init__()
        self.dem_layer = dict(dem_layer)
        self.dem_layer["metadata"] = dict(dem_layer.get("metadata", {}))
        self.criterion_layers = []
        for layer in criterion_layers:
            snapshot = dict(layer)
            snapshot["metadata"] = dict(layer.get("metadata", {}))
            self.criterion_layers.append(snapshot)
        self.model_settings = dict(model_settings)
        self.memory_budget_bytes = memory_budget_bytes

    def _is_cancelled(self) -> bool:
        return QThread.currentThread().isInterruptionRequested()

    def _on_progress(self, steps: int, elapsed: float, timestep: float) -> None:
        total_time = self.model_settings["total_time"]
        percent = min(100, int(round(100.0 * elapsed / total_time)))
        self.progress.emit(percent, elapsed, timestep)

    @pyqtSlot()
    def run(self) -> None:
        try:
            dem_path = self.dem_layer["path"]
            metadata = inspect_geotiff(dem_path, band=self.dem_layer.get("band", 1))
            estimated = estimate_reference_memory_bytes(
                metadata.width,
                metadata.height,
                criterion_count=len(self.criterion_layers),
            )
            if estimated > self.memory_budget_bytes:
                raise MemoryError(
                    f"estimated reference working memory is {estimated / 2**20:.0f} MiB, "
                    f"above the selected {self.memory_budget_bytes / 2**20:.0f} MiB budget"
                )
            if self._is_cancelled():
                self.cancelled.emit()
                return

            dem_grid = load_geotiff(dem_path, band=self.dem_layer.get("band", 1))
            if self._is_cancelled():
                self.cancelled.emit()
                return

            susceptibility = None
            if self.criterion_layers:
                criteria = {}
                weights = {}
                combined_valid = dem_grid.valid_mask.copy()
                for index, layer in enumerate(self.criterion_layers, start=1):
                    criterion_grid = load_geotiff(
                        layer["path"], band=layer.get("band", 1)
                    )
                    require_aligned(dem_grid, criterion_grid)
                    name = f"criterion_{index}"
                    criteria[name] = criterion_grid.data
                    weights[name] = float(layer["weight"])
                    combined_valid &= criterion_grid.valid_mask
                    del criterion_grid
                    if self._is_cancelled():
                        self.cancelled.emit()
                        return
                susceptibility = weighted_susceptibility_index(
                    criteria,
                    weights,
                    valid_mask=combined_valid,
                )
                del criteria, weights, combined_valid

            settings = self.model_settings
            model = ExnerTerrainModel(
                cell_size_x=dem_grid.cell_size_x,
                cell_size_y=dem_grid.cell_size_y,
                alpha=settings["alpha"],
                beta=settings["beta"],
                critical_slope_threshold=settings["critical_slope_threshold"],
                diffusion_tensor=np.array(
                    [
                        [settings["d_xx"], settings["d_xy"]],
                        [settings["d_xy"], settings["d_yy"]],
                    ],
                    dtype=np.float64,
                ),
                cfl=settings["cfl"],
                nodata=dem_grid.nodata,
            )
            simulation = model.simulate(
                dem_grid.data,
                total_time=settings["total_time"],
                max_timestep=settings["max_timestep"],
                valid_mask=dem_grid.valid_mask,
                progress=self._on_progress,
                cancel_requested=self._is_cancelled,
            )
            self.succeeded.emit(
                DesktopSimulationResult(
                    dem_path=dem_grid.path,
                    simulation=simulation,
                    susceptibility_index=susceptibility,
                    estimated_memory_bytes=estimated,
                    criterion_count=len(self.criterion_layers),
                    model_settings=dict(self.model_settings),
                    input_layers=[self.dem_layer, *self.criterion_layers],
                )
            )
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()
