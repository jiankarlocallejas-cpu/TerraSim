"""Native TerraSim desktop workbench.

This is the Qt entry point for the desktop-first rebuild. Scientific model
execution is intentionally kept out of this window until the implementation
matches the equations and calibration described in the TerraSim paper.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
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
        self.pages.addWidget(self._placeholder_page(
            "Results",
            "Simulation outputs and map layers will appear here when the paper-aligned model is connected.",
        ))
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
            "Add spatial inputs to the project. Source files stay at their original paths; "
            "the project records references to them."
        )
        description.setWordWrap(True)
        description.setObjectName("muted")
        layout.addWidget(description)

        actions = QHBoxLayout()
        add_button = QPushButton("Add files")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self._add_data_files)
        actions.addWidget(add_button)
        remove_button = QPushButton("Remove selected")
        remove_button.clicked.connect(self._remove_selected_layer)
        actions.addWidget(remove_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.layer_list = QListWidget()
        self.layer_list.setObjectName("layerList")
        layout.addWidget(self.layer_list, 1)

        self.data_hint = QLabel(
            "Supported inputs: GeoTIFF rasters, common vector GIS files, and CSV tables. "
            "Coordinate systems and raster alignment need to be checked before modeling."
        )
        self.data_hint.setWordWrap(True)
        self.data_hint.setObjectName("muted")
        layout.addWidget(self.data_hint)
        return page

    def _model_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        intro = QLabel(
            "Adjust relative transport strength for sensitivity exploration. These controls are "
            "multipliers; they are not claimed to be calibrated physical coefficient values."
        )
        intro.setWordWrap(True)
        intro.setObjectName("muted")
        layout.addWidget(intro)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(22, 18, 22, 18)
        panel_layout.setSpacing(12)
        alpha = ParameterControl(
            "α · Slope-driven transport",
            "Scales the paper's slope-driven transport response. Rainfall and runoff data may "
            "inform a recommendation once the conversion is defined and calibrated.",
        )
        beta = ParameterControl(
            "β · Background diffusion",
            "Scales background diffusion such as creep and rainsplash. Soil and cover properties "
            "can inform a sourced suggestion; this control remains adjustable.",
        )
        panel_layout.addWidget(alpha)
        panel_layout.addWidget(beta)
        layout.addWidget(panel)

        provenance = QFrame()
        provenance.setObjectName("notice")
        provenance_layout = QVBoxLayout(provenance)
        provenance_layout.setContentsMargins(20, 16, 20, 16)
        provenance_title = QLabel("Recommendations and calibration")
        provenance_title.setObjectName("sectionTitle")
        provenance_body = QLabel(
            "Soil datasets can support estimates of erodibility and critical shear stress. "
            "Those are related soil properties, not interchangeable with this paper's α and β. "
            "TerraSim will show the source and assumptions for any recommendation rather than "
            "silently converting one parameter into another."
        )
        provenance_body.setWordWrap(True)
        provenance_body.setObjectName("muted")
        provenance_layout.addWidget(provenance_title)
        provenance_layout.addWidget(provenance_body)
        layout.addWidget(provenance)
        layout.addStretch(1)

        self.alpha_control = alpha
        self.beta_control = beta
        return page

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
            "Add spatial input files",
            "",
            "Spatial data (*.tif *.tiff *.img *.shp *.gpkg *.geojson *.csv);;All files (*)",
        )
        for path in paths:
            resolved = str(Path(path).resolve())
            if any(layer["path"] == resolved for layer in self.layers):
                continue
            layer = {"path": resolved, "name": Path(resolved).name}
            self.layers.append(layer)
            self.layer_list.addItem(layer["name"])
        if paths:
            self.statusBar().showMessage(f"Added {len(paths)} input file(s)", 5000)

    def _remove_selected_layer(self) -> None:
        row = self.layer_list.currentRow()
        if row < 0:
            return
        self.layer_list.takeItem(row)
        del self.layers[row]

    def _new_project(self) -> None:
        self.project_path = None
        self.layers.clear()
        self.layer_list.clear()
        self.alpha_control.set_multiplier(1.0)
        self.beta_control.set_multiplier(1.0)
        self.project_label.setText("Untitled project")
        self.statusBar().showMessage("New project", 3000)

    def _open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open TerraSim project", "", "TerraSim project (*.terrasim.json *.json)"
        )
        if not path:
            return
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            self.layers = list(payload.get("layers", []))
            self.layer_list.clear()
            for layer in self.layers:
                self.layer_list.addItem(layer.get("name", Path(layer["path"]).name))
            controls = payload.get("model_controls", {})
            if isinstance(controls, dict):
                self.alpha_control.set_multiplier(controls.get("alpha_multiplier", 1.0))
                self.beta_control.set_multiplier(controls.get("beta_multiplier", 1.0))
            self.project_path = Path(path)
            self.project_label.setText(self.project_path.name)
            self.statusBar().showMessage("Project opened", 5000)
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
            "version": 1,
            "layers": self.layers,
            "model_controls": {
                "alpha_multiplier": self.alpha_control.multiplier,
                "beta_multiplier": self.beta_control.multiplier,
                "status": "exploratory; coefficients are not yet calibrated",
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
