from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QFormLayout,
    QComboBox,
    QPushButton,
    QSpinBox,
    QHBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QLineEdit,
    QCheckBox,
)

from app.services import GraphService


class ControlsPanel(QWidget):
    """
    Права панель керування:
    - вибір початкового та цільового міста;
    - запуск/паузи/кроки візуалізації;
    - налаштування затримки;
    - вмикання/вимикання карти України;
    - редагування графу (вершини/ребра).
    """

    # --- сигнали, які ловить MainWindow ---
    request_find_path = Signal(str, str)
    request_step = Signal()
    request_play = Signal()
    request_pause = Signal()
    request_reset_visualization = Signal()

    graph_changed = Signal()
    delay_changed = Signal(int)

    # --- сигнали зміни початкового/кінцевого міста ---
    source_city_changed = Signal(str)
    target_city_changed = Signal(str)

    # --- карта України ---
    map_visibility_changed = Signal(bool)

    def __init__(self, graph_service: GraphService, parent=None) -> None:
        super().__init__(parent)
        self._graph_service = graph_service

        self._init_ui()

    # ---------- побудова інтерфейсу ----------

    def _init_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setAlignment(Qt.AlignTop)

        # ---------- блок пошуку шляху ----------
        route_group = QGroupBox("Пошук найкоротшого шляху")
        route_form = QFormLayout()

        self.combo_source = QComboBox()
        self.combo_target = QComboBox()

        route_form.addRow("Початкове місто:", self.combo_source)
        route_form.addRow("Цільове місто:", self.combo_target)

        btn_layout = QHBoxLayout()
        self.btn_find = QPushButton("Знайти шлях")
        btn_layout.addWidget(self.btn_find)
        route_form.addRow(btn_layout)

        route_group.setLayout(route_form)
        root_layout.addWidget(route_group)

        # ---------- блок візуалізації ----------
        viz_group = QGroupBox("Візуалізація алгоритму Дейкстри")
        viz_layout = QVBoxLayout()

        controls_layout = QHBoxLayout()
        self.btn_step = QPushButton("Крок")
        self.btn_play = QPushButton("▶ Авто")
        self.btn_pause = QPushButton("⏸ Пауза")
        self.btn_reset = QPushButton("Скинути")

        controls_layout.addWidget(self.btn_step)
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_pause)
        controls_layout.addWidget(self.btn_reset)

        viz_layout.addLayout(controls_layout)

        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Затримка між кроками, мс:"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(50, 5000)
        self.delay_spin.setSingleStep(50)
        self.delay_spin.setValue(300)
        delay_layout.addWidget(self.delay_spin)

        viz_layout.addLayout(delay_layout)

        # чекбокс «Показувати карту України»
        self.map_checkbox = QCheckBox("Показувати карту України")
        self.map_checkbox.setChecked(True)
        viz_layout.addWidget(self.map_checkbox)

        viz_group.setLayout(viz_layout)
        root_layout.addWidget(viz_group)

        # ---------- блок редагування графу ----------
        graph_group = QGroupBox("Редагування графу")
        graph_layout = QVBoxLayout()

        # Додавання міста
        add_city_group = QGroupBox("Додати місто")
        add_city_form = QFormLayout()
        self.city_name_edit = QLineEdit()
        self.city_x_spin = QDoubleSpinBox()
        self.city_y_spin = QDoubleSpinBox()
        for spin in (self.city_x_spin, self.city_y_spin):
            spin.setRange(-1000.0, 2000.0)
            spin.setDecimals(1)
        self.city_x_spin.setValue(500.0)
        self.city_y_spin.setValue(400.0)
        self.btn_add_city = QPushButton("Додати місто")

        add_city_form.addRow("Назва:", self.city_name_edit)
        add_city_form.addRow("X:", self.city_x_spin)
        add_city_form.addRow("Y:", self.city_y_spin)
        add_city_form.addRow(self.btn_add_city)
        add_city_group.setLayout(add_city_form)

        # Видалення міста
        remove_city_group = QGroupBox("Видалити місто")
        remove_city_form = QFormLayout()
        self.combo_remove_city = QComboBox()
        self.btn_remove_city = QPushButton("Видалити місто")
        remove_city_form.addRow("Місто:", self.combo_remove_city)
        remove_city_form.addRow(self.btn_remove_city)
        remove_city_group.setLayout(remove_city_form)

        # Додавання дороги
        add_road_group = QGroupBox("Додати дорогу")
        add_road_form = QFormLayout()
        self.combo_road_from = QComboBox()
        self.combo_road_to = QComboBox()
        self.road_distance_spin = QDoubleSpinBox()
        self.road_distance_spin.setRange(1.0, 10000.0)
        self.road_distance_spin.setValue(100.0)
        self.btn_add_road = QPushButton("Додати дорогу")

        add_road_form.addRow("З міста:", self.combo_road_from)
        add_road_form.addRow("До міста:", self.combo_road_to)
        add_road_form.addRow("Відстань, км:", self.road_distance_spin)
        add_road_form.addRow(self.btn_add_road)
        add_road_group.setLayout(add_road_form)

        # Видалення дороги
        remove_road_group = QGroupBox("Видалити дорогу")
        remove_road_form = QFormLayout()
        self.combo_remove_road_from = QComboBox()
        self.combo_remove_road_to = QComboBox()
        self.btn_remove_road = QPushButton("Видалити дорогу")

        remove_road_form.addRow("З міста:", self.combo_remove_road_from)
        remove_road_form.addRow("До міста:", self.combo_remove_road_to)
        remove_road_form.addRow(self.btn_remove_road)
        remove_road_group.setLayout(remove_road_form)

        graph_layout.addWidget(add_city_group)
        graph_layout.addWidget(remove_city_group)
        graph_layout.addWidget(add_road_group)
        graph_layout.addWidget(remove_road_group)

        graph_group.setLayout(graph_layout)
        root_layout.addWidget(graph_group)

        root_layout.addStretch()

        # Підключення сигналів
        self._connect_signals()

    def _connect_signals(self) -> None:
        self.btn_find.clicked.connect(self._on_find_clicked)
        self.btn_step.clicked.connect(self.request_step.emit)
        self.btn_play.clicked.connect(self.request_play.emit)
        self.btn_pause.clicked.connect(self.request_pause.emit)
        self.btn_reset.clicked.connect(self.request_reset_visualization.emit)

        self.delay_spin.valueChanged.connect(self.delay_changed.emit)

        self.btn_add_city.clicked.connect(self._on_add_city)
        self.btn_remove_city.clicked.connect(self._on_remove_city)
        self.btn_add_road.clicked.connect(self._on_add_road)
        self.btn_remove_road.clicked.connect(self._on_remove_road)

        self.combo_source.currentTextChanged.connect(
            self.source_city_changed.emit
        )
        self.combo_target.currentTextChanged.connect(
            self.target_city_changed.emit
        )

        # карта
        self.map_checkbox.stateChanged.connect(
            lambda state: self.map_visibility_changed.emit(state == Qt.Checked)
        )

    # ---------- API для MainWindow ----------

    def update_cities(self, cities: List[str]) -> None:
        """
        Оновлює вміст усіх ComboBox з переліками міст.
        """
        combos = [
            self.combo_source,
            self.combo_target,
            self.combo_remove_city,
            self.combo_road_from,
            self.combo_road_to,
            self.combo_remove_road_from,
            self.combo_remove_road_to,
        ]
        for combo in combos:
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(cities)
            if current and current in cities:
                combo.setCurrentText(current)
            combo.blockSignals(False)

    # --- Методи, які викликає MainWindow у відповідь на кліки по Canvas ---

    def set_source_city(self, name: str) -> None:
        idx = self.combo_source.findText(name)
        if idx >= 0:
            self.combo_source.setCurrentIndex(idx)

    def set_target_city(self, name: str) -> None:
        idx = self.combo_target.findText(name)
        if idx >= 0:
            self.combo_target.setCurrentIndex(idx)

    def set_selected_city_for_edit(self, name: str) -> None:
        combos = [
            self.combo_remove_city,
            self.combo_road_from,
            self.combo_road_to,
            self.combo_remove_road_from,
            self.combo_remove_road_to,
        ]
        for combo in combos:
            idx = combo.findText(name)
            if idx >= 0:
                combo.setCurrentIndex(idx)

    def set_new_city_position(self, x: float, y: float) -> None:
        self.city_x_spin.setValue(x)
        self.city_y_spin.setValue(y)

    # ---------- внутрішні обробники ----------

    def _on_find_clicked(self) -> None:
        source = self.combo_source.currentText()
        target = self.combo_target.currentText()
        if not source or not target:
            return
        self.request_find_path.emit(source, target)

    def _on_add_city(self) -> None:
        name = self.city_name_edit.text().strip()
        x = self.city_x_spin.value()
        y = self.city_y_spin.value()
        if not name:
            return
        self._graph_service.add_city(name, x, y)
        self.city_name_edit.clear()
        self.graph_changed.emit()

    def _on_remove_city(self) -> None:
        name = self.combo_remove_city.currentText()
        if not name:
            return
        self._graph_service.remove_city(name)
        self.graph_changed.emit()

    def _on_add_road(self) -> None:
        source = self.combo_road_from.currentText()
        target = self.combo_road_to.currentText()
        distance = self.road_distance_spin.value()
        if not source or not target:
            return
        self._graph_service.add_road(source, target, distance)
        self.graph_changed.emit()

    def _on_remove_road(self) -> None:
        source = self.combo_remove_road_from.currentText()
        target = self.combo_remove_road_to.currentText()
        if not source or not target:
            return
        self._graph_service.remove_road(source, target)
        self.graph_changed.emit()
