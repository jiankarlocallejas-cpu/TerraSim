"""Native TerraSim desktop workbench.

Scientific models live in backend services; this window handles desktop input, settings, and results.
"""
from __future__ import annotations

import json
import sys

import numpy as np
from pathlib import Path
from typing import Any

from PyQt5.QtCore import QThread, Qt
from PyQt5.QtGui import QFont
from backend.services.paper_model import estimate_reference_memory_bytes
from backend.services.raster_inputs import (
    RasterInputError,
    RasterMetadata,
    alignment_errors,
    inspect_geotiff,
    require_aligned,
    save_geotiff,
)
from desktop.simulation_worker import DesktopSimulationResult, SimulationWorker

from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QFrame,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class ParameterControl(QWidget):
    """A clearly labeled relative model control, not an uncalibrated coefficient."""

    def __init__(self, title: str, description: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._value = 100
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)

        heading = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setObjectName("sectionTitle")
        self.value_label = QLabel("1.00×")
        self.value_label.setObjectName("parameterValue")
        heading.addWidget(self.title_label)
        heading.addStretch(1)
        heading.addWidget(self.value_label)
        layout.addLayout(heading)

        self.description_label = QLabel(description)
        self.description_label.setWordWrap(True)
        self.description_label.setObjectName("muted")
        layout.addWidget(self.description_label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(10, 300)
        self.slider.setValue(100)
        self.slider.valueChanged.connect(self._update_value)
        layout.addWidget(self.slider)

        bounds = QHBoxLayout()
        bounds.addWidget(QLabel("0.10×"))
        bounds.addStretch(1)
        bounds.addWidget(QLabel("3.00×"))
        layout.addLayout(bounds)

    def _update_value(self, value: int) -> None:
        self._value = value
        self.value_label.setText(f"{value / 100:.2f}×")

    @property
    def multiplier(self) -> float:
        return self._value / 100.0

    def set_multiplier(self, value: float) -> None:
        bounded = min(3.0, max(0.1, float(value)))
        self.slider.setValue(round(bounded * 100))


class TerraSimDesktop(QMainWindow):
    """Main window for TerraSim's native Qt desktop application."""

    PAGES = ("Overview", "Input Data", "Model Settings", "Scenarios", "Results")

    def __init__(self) -> None:
        super().__init__()
        self.project_path: Path | None = None
        self.layers: list[dict[str, Any]] = []
        self._simulation_thread: QThread | None = None
        self._simulation_worker: SimulationWorker | None = None
        self._last_result: DesktopSimulationResult | None = None
        self._close_when_simulation_finishes = False
        self._build_window()
        self._build_menu()
        self._show_page(0)

    def _build_window(self) -> None:
        self.setWindowTitle("TerraSim")
        self.resize(1440, 900)
        self.setMinimumSize(1080, 680)

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 24, 18, 18)
        sidebar_layout.setSpacing(8)

        brand = QLabel("TerraSim")
        brand.setObjectName("brand")
        sidebar_layout.addWidget(brand)
        subtitle = QLabel("SOIL EROSION WORKBENCH")
        subtitle.setObjectName("eyebrow")
        sidebar_layout.addWidget(subtitle)
        sidebar_layout.addSpacing(28)

        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        for page in self.PAGES:
            self.navigation.addItem(QListWidgetItem(page))
        self.navigation.currentRowChanged.connect(self._show_page)
        sidebar_layout.addWidget(self.navigation, 1)

        sidebar_note = QLabel("Desktop edition\nQt · GIS · Terrain modeling")
        sidebar_note.setObjectName("muted")
        sidebar_layout.addWidget(sidebar_note)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 24, 32, 20)
        content_layout.setSpacing(18)

        topbar = QHBoxLayout()
        self.breadcrumb = QLabel("Overview")
        self.breadcrumb.setObjectName("pageTitle")
        topbar.addWidget(self.breadcrumb)
        topbar.addStretch(1)
        self.project_label = QLabel("Untitled project")
        self.project_label.setObjectName("muted")
        topbar.addWidget(self.project_label)
        content_layout.addLayout(topbar)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._overview_page())
        self.pages.addWidget(self._data_page())
        self.pages.addWidget(self._model_page())
        self.pages.addWidget(self._placeholder_page(
            "Scenario comparison",
            "Set up baseline, rainfall, and vegetation scenarios after the model inputs are loaded.",
        ))
        self.pages.addWidget(self._results_page())
        content_layout.addWidget(self.pages, 1)

        self.statusBar().showMessage("Ready")
        root_layout.addWidget(sidebar)
        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)
        self.setStyleSheet(self._stylesheet())

    def _overview_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        intro = QFrame()
        intro.setObjectName("hero")
        intro_layout = QVBoxLayout(intro)
        intro_layout.setContentsMargins(26, 24, 26, 24)
        title = QLabel("A fresh workspace for terrain and erosion analysis")
        title.setObjectName("heroTitle")
        intro_layout.addWidget(title)
        copy = QLabel(
            "Start with a DEM and supporting soil, rainfall, and land-cover data. "
            "TerraSim will keep data preparation, model settings, scenarios, and results together."
        )
        copy.setWordWrap(True)
        copy.setObjectName("muted")
        intro_layout.addWidget(copy)
        open_data = QPushButton("Add input data")
        open_data.setObjectName("primaryButton")
        open_data.clicked.connect(lambda: self.navigation.setCurrentRow(1))
        intro_layout.addWidget(open_data, 0, Qt.AlignLeft)
        layout.addWidget(intro)

        cards = QHBoxLayout()
        cards.addWidget(self._stat_card("INPUT LAYERS", "0", "DEM, soil, rainfall, cover"))
        cards.addWidget(self._stat_card("SCENARIOS", "0", "Baseline and alternatives"))
        cards.addWidget(self._stat_card("MODEL STATUS", "Not run", "Configure inputs first"))
        layout.addLayout(cards)

        note = QFrame()
        note.setObjectName("notice")
        note_layout = QVBoxLayout(note)
        note_layout.setContentsMargins(20, 16, 20, 16)
        note_title = QLabel("Model parameters will be explicit")
        note_title.setObjectName("sectionTitle")
        note_body = QLabel(
            "The paper's transport coefficients are not yet calibrated from the available files. "
            "The interface will distinguish source-based soil suggestions from user-adjustable "
            "α and β controls, and will identify provisional settings."
        )
        note_body.setWordWrap(True)
        note_body.setObjectName("muted")
        note_layout.addWidget(note_title)
        note_layout.addWidget(note_body)
        layout.addWidget(note)
        layout.addStretch(1)
        return page

    def _data_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        description = QLabel(
            "Add GeoTIFF rasters. TerraSim checks spatial metadata before reading pixel data, "
            "so adding a large file does not load it into memory."
        )
        description.setWordWrap(True)
        description.setObjectName("muted")
        layout.addWidget(description)

        actions = QHBoxLayout()
        add_button = QPushButton("Add GeoTIFF")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self._add_data_files)
        actions.addWidget(add_button)
        self.set_dem_button = QPushButton("Set as DEM")
        self.set_dem_button.clicked.connect(lambda: self._set_layer_role("elevation"))
        actions.addWidget(self.set_dem_button)
        self.set_criterion_button = QPushButton("Set as criterion")
        self.set_criterion_button.clicked.connect(lambda: self._set_layer_role("criterion"))
        actions.addWidget(self.set_criterion_button)
        remove_button = QPushButton("Remove selected")
        remove_button.clicked.connect(self._remove_selected_layer)
        actions.addWidget(remove_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.layer_list = QListWidget()
        self.layer_list.setObjectName("layerList")
        self.layer_list.currentRowChanged.connect(self._update_layer_actions)
        layout.addWidget(self.layer_list, 1)

        weight_row = QHBoxLayout()
        weight_label = QLabel(
            "Selected criterion weight · all criterion weights must sum to 1.0000"
        )
        weight_label.setObjectName("muted")
        weight_row.addWidget(weight_label)
        self.criterion_weight_control = QDoubleSpinBox()
        self.criterion_weight_control.setDecimals(4)
        self.criterion_weight_control.setRange(0.0, 1.0)
        self.criterion_weight_control.setSingleStep(0.05)
        self.criterion_weight_control.setEnabled(False)
        self.criterion_weight_control.valueChanged.connect(self._update_selected_weight)
        weight_row.addWidget(self.criterion_weight_control)
        layout.addLayout(weight_row)

        self.data_hint = QLabel()
        self.data_hint.setWordWrap(True)
        self.data_hint.setObjectName("muted")
        layout.addWidget(self.data_hint)
        self._refresh_layer_list()
        return page

    def _model_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        intro = QLabel(
            "The Python reference solver evolves terrain by sediment-flux divergence. "
            "Enter coefficients and time units from a calibration or mark them as exploratory. "
            "The paper does not provide a validated soil-to-α/β conversion."
        )
        intro.setWordWrap(True)
        intro.setObjectName("muted")
        layout.addWidget(intro)

        def numeric_input(value: float, step: float, decimals: int = 6) -> QDoubleSpinBox:
            control = QDoubleSpinBox()
            control.setDecimals(decimals)
            control.setRange(0.0, 1e12)
            control.setSingleStep(step)
            control.setValue(value)
            return control

        coefficients = QFrame()
        coefficients.setObjectName("panel")
        coefficient_layout = QVBoxLayout(coefficients)
        coefficient_layout.setContentsMargins(22, 18, 22, 18)
        coefficient_layout.setSpacing(8)
        coefficient_title = QLabel("Transport coefficients")
        coefficient_title.setObjectName("sectionTitle")
        coefficient_layout.addWidget(coefficient_title)
        coefficient_form = QFormLayout()
        self.alpha_base_spin = numeric_input(0.0, 0.01, 8)
        self.beta_base_spin = numeric_input(0.0, 0.01, 8)
        coefficient_form.addRow("Base α value · user supplied", self.alpha_base_spin)
        coefficient_form.addRow("Base β value · user supplied", self.beta_base_spin)
        coefficient_layout.addLayout(coefficient_form)
        self.alpha_control = ParameterControl(
            "α sensitivity multiplier",
            "Exploratory multiplier applied to the base coefficient above.",
        )
        self.beta_control = ParameterControl(
            "β sensitivity multiplier",
            "Exploratory multiplier applied to the base coefficient above.",
        )
        coefficient_layout.addWidget(self.alpha_control)
        coefficient_layout.addWidget(self.beta_control)
        layout.addWidget(coefficients)

        physics = QFrame()
        physics.setObjectName("panel")
        physics_layout = QVBoxLayout(physics)
        physics_layout.setContentsMargins(22, 18, 22, 18)
        physics_title = QLabel("Terrain transport")
        physics_title.setObjectName("sectionTitle")
        physics_layout.addWidget(physics_title)
        physics_form = QFormLayout()
        self.critical_slope_spin = numeric_input(0.0, 0.001, 8)
        self.d_xx_spin = numeric_input(1.0, 0.05, 6)
        self.d_xy_spin = QDoubleSpinBox()
        self.d_xy_spin.setDecimals(6)
        self.d_xy_spin.setRange(-1e6, 1e6)
        self.d_xy_spin.setSingleStep(0.05)
        self.d_xy_spin.setValue(0.0)
        self.d_yy_spin = numeric_input(1.0, 0.05, 6)
        physics_form.addRow("Critical slope term Sᶜ", self.critical_slope_spin)
        physics_form.addRow("Diffusion tensor Dₓₓ", self.d_xx_spin)
        physics_form.addRow("Diffusion tensor Dₓᵧ", self.d_xy_spin)
        physics_form.addRow("Diffusion tensor Dᵧᵧ", self.d_yy_spin)
        physics_layout.addLayout(physics_form)
        physics_note = QLabel(
            "D is dimensionless here. The identity tensor is an explicit starting assumption; "
            "adjust it only with a sourced rationale."
        )
        physics_note.setWordWrap(True)
        physics_note.setObjectName("muted")
        physics_layout.addWidget(physics_note)
        layout.addWidget(physics)

        run_panel = QFrame()
        run_panel.setObjectName("panel")
        run_layout = QVBoxLayout(run_panel)
        run_layout.setContentsMargins(22, 18, 22, 18)
        run_title = QLabel("Run controls")
        run_title.setObjectName("sectionTitle")
        run_layout.addWidget(run_title)
        run_form = QFormLayout()
        self.total_time_spin = numeric_input(1.0, 0.1, 6)
        self.max_timestep_spin = numeric_input(0.1, 0.01, 8)
        self.cfl_spin = QDoubleSpinBox()
        self.cfl_spin.setDecimals(3)
        self.cfl_spin.setRange(0.001, 1.0)
        self.cfl_spin.setSingleStep(0.05)
        self.cfl_spin.setValue(0.25)
        self.memory_budget_spin = QDoubleSpinBox()
        self.memory_budget_spin.setDecimals(0)
        self.memory_budget_spin.setRange(64, 65536)
        self.memory_budget_spin.setSingleStep(128)
        self.memory_budget_spin.setValue(512)
        self.memory_budget_spin.setSuffix(" MiB")
        run_form.addRow("Total duration · model time units", self.total_time_spin)
        run_form.addRow("Maximum time step", self.max_timestep_spin)
        run_form.addRow("CFL safety factor", self.cfl_spin)
        run_form.addRow("Memory budget · approximate", self.memory_budget_spin)
        run_layout.addLayout(run_form)

        actions = QHBoxLayout()
        self.run_button = QPushButton("Run terrain simulation")
        self.run_button.setObjectName("primaryButton")
        self.run_button.clicked.connect(self._start_simulation)
        actions.addWidget(self.run_button)
        self.cancel_button = QPushButton("Cancel run")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self._cancel_simulation)
        actions.addWidget(self.cancel_button)
        actions.addStretch(1)
        run_layout.addLayout(actions)
        self.run_progress = QProgressBar()
        self.run_progress.setRange(0, 100)
        self.run_progress.setValue(0)
        run_layout.addWidget(self.run_progress)
        self.run_status = QLabel("No simulation run yet.")
        self.run_status.setWordWrap(True)
        self.run_status.setObjectName("muted")
        run_layout.addWidget(self.run_status)
        layout.addWidget(run_panel)
        layout.addStretch(1)
        return page

    def _results_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        summary_panel = QFrame()
        summary_panel.setObjectName("panel")
        summary_layout = QVBoxLayout(summary_panel)
        summary_layout.setContentsMargins(24, 22, 24, 22)
        heading = QLabel("Latest run")
        heading.setObjectName("sectionTitle")
        summary_layout.addWidget(heading)
        self.results_summary = QLabel(
            "No results yet. Load a DEM and configure a reference run in Model Settings."
        )
        self.results_summary.setWordWrap(True)
        self.results_summary.setObjectName("muted")
        summary_layout.addWidget(self.results_summary)
        layout.addWidget(summary_panel)

        exports = QHBoxLayout()
        self.export_elevation_button = QPushButton("Export final elevation GeoTIFF")
        self.export_elevation_button.clicked.connect(self._export_elevation)
        self.export_elevation_button.setEnabled(False)
        exports.addWidget(self.export_elevation_button)
        self.export_susceptibility_button = QPushButton("Export susceptibility GeoTIFF")
        self.export_susceptibility_button.clicked.connect(self._export_susceptibility)
        self.export_susceptibility_button.setEnabled(False)
        exports.addWidget(self.export_susceptibility_button)
        exports.addStretch(1)
        layout.addLayout(exports)
        layout.addStretch(1)
        return page

    def _start_simulation(self) -> None:
        if self._simulation_thread is not None and self._simulation_thread.isRunning():
            return
        dems = [
            layer
            for layer in self.layers
            if layer.get("valid") and layer.get("role") == "elevation"
        ]
        if len(dems) != 1:
            QMessageBox.warning(
                self,
                "DEM required",
                "Assign exactly one valid projected GeoTIFF as the DEM before running.",
            )
            return
        dem = dems[0]
        criteria = [
            layer
            for layer in self.layers
            if layer.get("valid") and layer.get("role") == "criterion"
        ]
        try:
            dem_metadata = self._metadata_for_layer(dem)
            for layer in criteria:
                require_aligned(dem_metadata, self._metadata_for_layer(layer))
            if criteria:
                weight_sum = sum(float(layer.get("weight", 0.0)) for layer in criteria)
                if abs(weight_sum - 1.0) > 1e-9:
                    raise ValueError(
                        f"criterion weights sum to {weight_sum:.4f}; set the total to 1.0000"
                    )
        except (RasterInputError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "Input validation failed", str(exc))
            return

        estimated = estimate_reference_memory_bytes(
            dem_metadata.width,
            dem_metadata.height,
            criterion_count=len(criteria),
        )
        budget = int(self.memory_budget_spin.value() * 2**20)
        if estimated > budget:
            QMessageBox.warning(
                self,
                "Memory budget exceeded",
                f"The reference solver estimates {estimated / 2**20:.0f} MiB of working "
                f"memory, above the selected {budget / 2**20:.0f} MiB budget. "
                "Use a smaller raster; tiled processing is not available yet.",
            )
            return

        settings = {
            "alpha": self.alpha_base_spin.value() * self.alpha_control.multiplier,
            "beta": self.beta_base_spin.value() * self.beta_control.multiplier,
            "critical_slope_threshold": self.critical_slope_spin.value(),
            "d_xx": self.d_xx_spin.value(),
            "d_xy": self.d_xy_spin.value(),
            "d_yy": self.d_yy_spin.value(),
            "cfl": self.cfl_spin.value(),
            "total_time": self.total_time_spin.value(),
            "max_timestep": self.max_timestep_spin.value(),
        }
        self.run_progress.setValue(0)
        self.run_status.setText(
            f"Loading {dem['name']} · estimated reference working memory "
            f"{estimated / 2**20:.1f} MiB."
        )
        self.statusBar().showMessage("Simulation started")

        thread = QThread(self)
        worker = SimulationWorker(dem, criteria, settings, memory_budget_bytes=budget)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._update_simulation_progress)
        worker.succeeded.connect(self._simulation_completed)
        worker.failed.connect(self._simulation_failed)
        worker.cancelled.connect(self._simulation_cancelled)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._simulation_thread_finished)
        thread.finished.connect(thread.deleteLater)
        self._simulation_thread = thread
        self._simulation_worker = worker
        self.run_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        thread.start()

    def _cancel_simulation(self) -> None:
        if self._simulation_thread is not None and self._simulation_thread.isRunning():
            self._simulation_thread.requestInterruption()
            self.cancel_button.setEnabled(False)
            self.run_status.setText("Cancellation requested; stopping after the current step.")

    def _update_simulation_progress(
        self, percent: int, elapsed: float, timestep: float
    ) -> None:
        self.run_progress.setValue(percent)
        self.run_status.setText(
            f"Running · elapsed {elapsed:.6g} model time units · "
            f"last step {timestep:.6g}"
        )

    def _simulation_completed(self, result: DesktopSimulationResult) -> None:
        self._last_result = result
        simulation = result.simulation
        run_state = "Cancelled at requested checkpoint" if simulation.cancelled else "Completed"
        susceptibility_text = "not calculated"
        if result.susceptibility_index is not None:
            valid_index = result.susceptibility_index[
                np.isfinite(result.susceptibility_index)
            ]
            if valid_index.size:
                susceptibility_text = (
                    f"{result.criterion_count} criterion raster(s) · "
                    f"range {float(np.min(valid_index)):.4f}–"
                    f"{float(np.max(valid_index)):.4f}"
                )
        self.results_summary.setText(
            f"{run_state}\n"
            f"DEM: {Path(result.dem_path).name}\n"
            f"Steps: {simulation.step_count} · elapsed: {simulation.elapsed_time:.6g} "
            "model time units\n"
            f"Smallest stability limit observed: {simulation.min_stable_timestep:.6g}\n"
            f"Estimated working memory: {result.estimated_memory_bytes / 2**20:.1f} MiB\n"
            f"Elevation-volume change: {simulation.mass_after - simulation.mass_before:.6g} "
            "m³ under closed no-flux boundaries\n"
            f"Maximum single-step elevation change: "
            f"{simulation.max_abs_step_change:.6g} m\n"
            f"Weighted susceptibility: {susceptibility_text}"
        )
        self.export_elevation_button.setEnabled(True)
        self.export_susceptibility_button.setEnabled(
            result.susceptibility_index is not None
        )
        self.run_status.setText(run_state)
        self.statusBar().showMessage(run_state, 5000)
        self.navigation.setCurrentRow(4)

    def _simulation_failed(self, message: str) -> None:
        self.run_status.setText(f"Run failed · {message}")
        self.statusBar().showMessage("Simulation failed", 5000)
        QMessageBox.warning(self, "Simulation failed", message)

    def _simulation_cancelled(self) -> None:
        self.run_status.setText("Cancelled before simulation began.")
        self.statusBar().showMessage("Simulation cancelled", 5000)

    def _simulation_thread_finished(self) -> None:
        self.run_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self._simulation_thread = None
        self._simulation_worker = None
        if self._close_when_simulation_finishes:
            self._close_when_simulation_finishes = False
            self.close()

    def closeEvent(self, event) -> None:
        thread = self._simulation_thread
        if thread is not None and thread.isRunning():
            self._close_when_simulation_finishes = True
            thread.requestInterruption()
            self.cancel_button.setEnabled(False)
            self.run_status.setText(
                "Closing after cancellation at the current simulation checkpoint."
            )
            event.ignore()
            return
        event.accept()

    def _export_elevation(self) -> None:
        if self._last_result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export final elevation", "", "GeoTIFF (*.tif)"
        )
        if not path:
            return
        if not path.lower().endswith((".tif", ".tiff")):
            path += ".tif"
        try:
            saved = save_geotiff(
                self._last_result.dem_path,
                path,
                self._last_result.simulation.elevation,
                self._last_result.simulation.valid_mask,
            )
            self.statusBar().showMessage(f"Saved {Path(saved).name}", 5000)
        except (OSError, RasterInputError) as exc:
            QMessageBox.warning(self, "Could not export elevation", str(exc))

    def _export_susceptibility(self) -> None:
        if self._last_result is None or self._last_result.susceptibility_index is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export susceptibility index", "", "GeoTIFF (*.tif)"
        )
        if not path:
            return
        if not path.lower().endswith((".tif", ".tiff")):
            path += ".tif"
        index = self._last_result.susceptibility_index
        try:
            saved = save_geotiff(
                self._last_result.dem_path,
                path,
                index,
                np.isfinite(index),
            )
            self.statusBar().showMessage(f"Saved {Path(saved).name}", 5000)
        except (OSError, RasterInputError) as exc:
            QMessageBox.warning(self, "Could not export susceptibility", str(exc))

    def _placeholder_page(self, title: str, copy: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)
        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        body = QLabel(copy)
        body.setWordWrap(True)
        body.setObjectName("muted")
        panel_layout.addWidget(heading)
        panel_layout.addWidget(body)
        layout.addWidget(panel)
        layout.addStretch(1)
        return page

    def _stat_card(self, label: str, value: str, detail: str) -> QFrame:
        card = QFrame()
        card.setObjectName("statCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        eyebrow = QLabel(label)
        eyebrow.setObjectName("eyebrow")
        number = QLabel(value)
        number.setObjectName("statValue")
        caption = QLabel(detail)
        caption.setObjectName("muted")
        card_layout.addWidget(eyebrow)
        card_layout.addWidget(number)
        card_layout.addWidget(caption)
        return card

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        new_action = QAction("New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        open_action = QAction("Open Project…", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        save_action = QAction("Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction("Quit", self.close)

    def _show_page(self, index: int) -> None:
        if index < 0:
            return
        self.pages.setCurrentIndex(index)
        self.breadcrumb.setText(self.PAGES[index])

    def _add_data_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Add elevation or criterion GeoTIFFs",
            "",
            "GeoTIFF rasters (*.tif *.tiff);;All files (*)",
        )
        for path in paths:
            self._register_raster_path(path)
        if paths:
            self.statusBar().showMessage(f"Inspected {len(paths)} raster file(s)", 5000)

    def _register_raster_path(
        self,
        path: str,
        preferred_role: str | None = None,
        preferred_weight: float | None = None,
    ) -> None:
        resolved = (
            str(path)
            if str(path).startswith("/vsi")
            else str(Path(path).expanduser().resolve())
        )
        if any(layer.get("path") == resolved for layer in self.layers):
            return
        layer: dict[str, Any] = {
            "path": resolved,
            "name": Path(resolved).name,
            "role": "unassigned",
            "valid": False,
            "weight": 0.0,
        }
        try:
            metadata = inspect_geotiff(resolved)
            role = preferred_role if preferred_role in {"elevation", "criterion"} else None
            if role is None:
                role = (
                    "elevation"
                    if not any(
                        item.get("valid") and item.get("role") == "elevation"
                        for item in self.layers
                    )
                    else "criterion"
                )
            if role == "elevation":
                for existing in self.layers:
                    if existing.get("role") == "elevation":
                        existing["role"] = "criterion"
                        existing["weight"] = 0.0
            layer.update(
                {
                    "role": role,
                    "valid": True,
                    "weight": (
                        max(0.0, min(1.0, float(preferred_weight)))
                        if role == "criterion" and preferred_weight is not None
                        else 0.0
                    ),
                    "metadata": {
                        "width": metadata.width,
                        "height": metadata.height,
                        "crs": metadata.crs,
                        "transform": list(metadata.transform),
                        "cell_size_x": metadata.cell_size_x,
                        "cell_size_y": metadata.cell_size_y,
                        "units": metadata.units,
                        "nodata": metadata.nodata,
                        "band": metadata.band,
                        "dtype": metadata.dtype,
                    },
                }
            )
        except RasterInputError as exc:
            layer["error"] = str(exc)
        self.layers.append(layer)
        self._refresh_layer_list()

    @staticmethod
    def _metadata_for_layer(layer: dict[str, Any]) -> RasterMetadata:
        values = layer["metadata"]
        return RasterMetadata(
            path=layer["path"],
            width=values["width"],
            height=values["height"],
            crs=values["crs"],
            transform=tuple(values["transform"]),
            cell_size_x=values["cell_size_x"],
            cell_size_y=values["cell_size_y"],
            units=values["units"],
            nodata=values.get("nodata"),
            band=values.get("band", 1),
            dtype=values["dtype"],
        )

    def _refresh_layer_list(self) -> None:
        if not hasattr(self, "layer_list"):
            return
        self.layer_list.clear()
        dem = next(
            (
                layer
                for layer in self.layers
                if layer.get("valid") and layer.get("role") == "elevation"
            ),
            None,
        )
        for layer in self.layers:
            if not layer.get("valid"):
                label = f"Needs attention · {layer['name']} · {layer.get('error', 'invalid raster')}"
            else:
                metadata = self._metadata_for_layer(layer)
                role = (
                    "DEM"
                    if layer.get("role") == "elevation"
                    else f"Criterion · w={layer.get('weight', 0.0):.4f}"
                )
                label = (
                    f"{role} · {layer['name']} · "
                    f"{metadata.width} × {metadata.height} · "
                    f"{metadata.cell_size_x:g} × {metadata.cell_size_y:g} m · "
                    f"{metadata.crs}"
                )
                if dem is not None and layer.get("role") == "criterion":
                    mismatches = alignment_errors(
                        self._metadata_for_layer(dem), metadata
                    )
                    if mismatches:
                        label += " · not aligned"
            self.layer_list.addItem(QListWidgetItem(label))
        self._update_layer_actions()

        if dem is None:
            self.data_hint.setText(
                "No DEM assigned. Add a projected metric GeoTIFF and set one raster as the DEM."
            )
            return
        dem_metadata = self._metadata_for_layer(dem)
        mismatches = []
        for layer in self.layers:
            if layer.get("valid") and layer.get("role") == "criterion":
                issues = alignment_errors(
                    dem_metadata, self._metadata_for_layer(layer)
                )
                if issues:
                    mismatches.append(f"{layer['name']}: {'; '.join(issues)}")
        if mismatches:
            self.data_hint.setText(
                "DEM metadata is valid, but these criteria need matching CRS, dimensions, "
                "and pixel alignment before they can be combined: "
                + " | ".join(mismatches)
            )
        else:
            criteria = [
                layer
                for layer in self.layers
                if layer.get("valid") and layer.get("role") == "criterion"
            ]
            weight_sum = sum(float(layer.get("weight", 0.0)) for layer in criteria)
            if criteria and abs(weight_sum - 1.0) > 1e-9:
                criteria_status = (
                    f"{len(criteria)} aligned criterion raster(s); weights sum "
                    f"to {weight_sum:.4f} and must total 1.0000."
                )
            elif criteria:
                criteria_status = (
                    f"{len(criteria)} aligned criterion raster(s) with weights totaling 1.0000. "
                    "Criterion values must already be normalized to [0, 1]."
                )
            else:
                criteria_status = "No criteria assigned; the MCE overlay will be skipped."
            self.data_hint.setText(
                f"DEM ready · {dem_metadata.width} × {dem_metadata.height} cells · "
                f"{dem_metadata.cell_size_x:g} × {dem_metadata.cell_size_y:g} m · "
                f"{criteria_status} Reprojection and resampling are not automatic."
            )

    def _update_layer_actions(self, *_args: Any) -> None:
        if not hasattr(self, "layer_list"):
            return
        row = self.layer_list.currentRow()
        selected = 0 <= row < len(self.layers) and self.layers[row].get("valid", False)
        self.set_dem_button.setEnabled(selected)
        self.set_criterion_button.setEnabled(selected)
        is_criterion = selected and self.layers[row].get("role") == "criterion"
        self.criterion_weight_control.blockSignals(True)
        self.criterion_weight_control.setEnabled(is_criterion)
        self.criterion_weight_control.setValue(
            float(self.layers[row].get("weight", 0.0)) if is_criterion else 0.0
        )
        self.criterion_weight_control.blockSignals(False)

    def _set_layer_role(self, role: str) -> None:
        row = self.layer_list.currentRow()
        if not (0 <= row < len(self.layers)) or not self.layers[row].get("valid"):
            return
        if role == "elevation":
            for layer in self.layers:
                if layer.get("role") == "elevation":
                    layer["role"] = "criterion"
                    layer["weight"] = 0.0
        self.layers[row]["role"] = role
        if role == "criterion":
            self.layers[row].setdefault("weight", 0.0)
        elif role == "elevation":
            self.layers[row]["weight"] = 0.0
        self._refresh_layer_list()
        self.layer_list.setCurrentRow(row)

    def _update_selected_weight(self, value: float) -> None:
        row = self.layer_list.currentRow()
        if 0 <= row < len(self.layers) and self.layers[row].get("role") == "criterion":
            self.layers[row]["weight"] = float(value)
            self._refresh_layer_list()
            self.layer_list.setCurrentRow(row)

    def _remove_selected_layer(self) -> None:
        row = self.layer_list.currentRow()
        if row < 0:
            return
        self.layer_list.takeItem(row)
        del self.layers[row]
        self._refresh_layer_list()

    def _new_project(self) -> None:
        self.project_path = None
        self.layers.clear()
        self.layer_list.clear()
        self.alpha_control.set_multiplier(1.0)
        self.beta_control.set_multiplier(1.0)
        self.alpha_base_spin.setValue(0.0)
        self.beta_base_spin.setValue(0.0)
        self.critical_slope_spin.setValue(0.0)
        self.d_xx_spin.setValue(1.0)
        self.d_xy_spin.setValue(0.0)
        self.d_yy_spin.setValue(1.0)
        self.total_time_spin.setValue(1.0)
        self.max_timestep_spin.setValue(0.1)
        self.cfl_spin.setValue(0.25)
        self.memory_budget_spin.setValue(512)
        self.project_label.setText("Untitled project")
        self._refresh_layer_list()
        self.statusBar().showMessage("New project", 3000)

    def _open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open TerraSim project", "", "TerraSim project (*.terrasim.json *.json)"
        )
        if not path:
            return
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            saved_layers = list(payload.get("layers", []))
            self.layers.clear()
            self.layer_list.clear()
            for layer in saved_layers:
                if layer.get("path"):
                    self._register_raster_path(
                        layer["path"],
                        preferred_role=layer.get("role"),
                        preferred_weight=layer.get("weight"),
                    )
            controls = payload.get("model_controls", {})
            if isinstance(controls, dict):
                self.alpha_control.set_multiplier(controls.get("alpha_multiplier", 1.0))
                self.beta_control.set_multiplier(controls.get("beta_multiplier", 1.0))
                self.alpha_base_spin.setValue(float(controls.get("alpha_base", 0.0)))
                self.beta_base_spin.setValue(float(controls.get("beta_base", 0.0)))
                self.critical_slope_spin.setValue(float(controls.get("critical_slope_threshold", 0.0)))
                self.d_xx_spin.setValue(float(controls.get("d_xx", 1.0)))
                self.d_xy_spin.setValue(float(controls.get("d_xy", 0.0)))
                self.d_yy_spin.setValue(float(controls.get("d_yy", 1.0)))
                self.total_time_spin.setValue(float(controls.get("total_time", 1.0)))
                self.max_timestep_spin.setValue(float(controls.get("max_timestep", 0.1)))
                self.cfl_spin.setValue(float(controls.get("cfl", 0.25)))
                self.memory_budget_spin.setValue(float(controls.get("memory_budget_mib", 512)))
            self.project_path = Path(path)
            self.project_label.setText(self.project_path.name)
            self._refresh_layer_list()
            self.statusBar().showMessage("Project opened and raster metadata refreshed", 5000)
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            QMessageBox.critical(self, "Could not open project", str(exc))

    def _save_project(self) -> None:
        path = str(self.project_path) if self.project_path else ""
        if not path:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save TerraSim project", "", "TerraSim project (*.terrasim.json)"
            )
        if not path:
            return
        if not path.endswith(".terrasim.json"):
            path += ".terrasim.json"
        payload = {
            "format": "terrasim-project",
            "version": 2,
            "layers": self.layers,
            "model_controls": {
                "alpha_multiplier": self.alpha_control.multiplier,
                "beta_multiplier": self.beta_control.multiplier,
                "alpha_base": self.alpha_base_spin.value(),
                "beta_base": self.beta_base_spin.value(),
                "critical_slope_threshold": self.critical_slope_spin.value(),
                "d_xx": self.d_xx_spin.value(),
                "d_xy": self.d_xy_spin.value(),
                "d_yy": self.d_yy_spin.value(),
                "total_time": self.total_time_spin.value(),
                "max_timestep": self.max_timestep_spin.value(),
                "cfl": self.cfl_spin.value(),
                "memory_budget_mib": self.memory_budget_spin.value(),
                "status": "user supplied or exploratory; coefficients are not yet calibrated",
            },
        }
        try:
            Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
            self.project_path = Path(path)
            self.project_label.setText(self.project_path.name)
            self.statusBar().showMessage("Project saved", 5000)
        except OSError as exc:
            QMessageBox.critical(self, "Could not save project", str(exc))

    @staticmethod
    def _stylesheet() -> str:
        return """
            QWidget { background: #f4f6f8; color: #18212b; font-size: 10pt; }
            QMainWindow { background: #f4f6f8; }
            QMenuBar { background: #ffffff; padding: 6px; }
            QMenuBar::item { padding: 6px 10px; }
            QMenu { background: #ffffff; }
            QStatusBar { background: #ffffff; color: #657181; }
            #sidebar { background: #14212b; color: #f4f7fa; }
            #sidebar QLabel { background: transparent; }
            #brand { color: #ffffff; font-size: 22pt; font-weight: 700; }
            #eyebrow { color: #8293a1; font-size: 8pt; font-weight: 700; }
            #sidebar #eyebrow { color: #8ba0af; }
            #navigation { background: transparent; border: 0; outline: 0; color: #cad4dc; }
            #navigation::item { padding: 12px; border-radius: 7px; }
            #navigation::item:selected { background: #28404e; color: white; }
            #pageTitle { font-size: 19pt; font-weight: 650; }
            #hero, #panel, #statCard, #notice {
                background: white; border: 1px solid #e1e6eb; border-radius: 10px;
            }
            #hero { background: #eaf2f3; }
            #heroTitle { font-size: 21pt; font-weight: 650; }
            #sectionTitle { font-size: 12pt; font-weight: 650; }
            #statValue { font-size: 20pt; font-weight: 650; color: #1d6b65; }
            #parameterValue { color: #1d6b65; font-weight: 700; }
            #muted { color: #637181; }
            QPushButton {
                background: white; border: 1px solid #d7dee5; border-radius: 6px;
                padding: 9px 13px;
            }
            QPushButton:hover { background: #edf2f5; }
            #primaryButton {
                background: #1d6b65; color: white; border: 0; font-weight: 650;
            }
            #primaryButton:hover { background: #185954; }
            QSlider::groove:horizontal { height: 5px; background: #dfe5e9; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #1d6b65; border-radius: 2px; }
            QSlider::handle:horizontal {
                background: white; border: 2px solid #1d6b65; width: 14px;
                margin: -6px 0; border-radius: 8px;
            }
            #layerList { background: white; border: 1px solid #e1e6eb; border-radius: 8px; }
        """


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = TerraSimDesktop()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()




