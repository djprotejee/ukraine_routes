from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QTextEdit,
    QMessageBox,
)

from app.models.data_loader import load_graph
from app.services import GraphService, PathService
from .graph_canvas import GraphCanvas
from .controls_panel import ControlsPanel


class MainWindow(QMainWindow):
    """
    Головне вікно програми.
    Зліва: граф + результат під ним.
    Справа: панель керування.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Найкоротші шляхи автошляхами України (Дейкстра)")

        # Завантажуємо граф з файлів
        try:
            self._graph = load_graph()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(
                self,
                "Помилка завантаження даних",
                f"Не вдалося завантажити граф: {exc}",
            )
            raise

        self._graph_service = GraphService(self._graph)
        self._path_service = PathService(self._graph)

        self._init_ui()
        self._connect_signals()

        self.resize(1200, 800)

    def _init_ui(self) -> None:
        central = QWidget(self)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal, central)

        # ---- Ліва частина: граф + результат під ним ----
        left_container = QWidget(splitter)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.setSpacing(6)

        self.graph_canvas = GraphCanvas(self._graph_service.graph)
        left_layout.addWidget(self.graph_canvas, stretch=4)

        # Вікно з результатом під графом
        self.result_view = QTextEdit(left_container)
        self.result_view.setReadOnly(True)
        self.result_view.setMinimumHeight(110)
        self.result_view.setMaximumHeight(180)
        self.result_view.setPlaceholderText("Тут буде показано знайдений маршрут.")
        left_layout.addWidget(self.result_view, stretch=1)

        splitter.addWidget(left_container)

        # ---- Права частина: панель керування ----
        self.controls = ControlsPanel(self._graph_service)
        splitter.addWidget(self.controls)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        root_layout.addWidget(splitter)
        self.setCentralWidget(central)

        # Початкове відображення графа
        self.graph_canvas.refresh()

        # Список міст
        cities = self._graph_service.list_cities()

        # Передамо список міст у панель
        self.controls.update_cities(cities)

        # --- дефолтний маршрут, наприклад Ужгород → Луганськ ---
        default_source = "Ужгород"
        default_target = "Луганськ"

        if default_source in cities:
            self.controls.set_source_city(default_source)
            self.graph_canvas.set_source_city(default_source)
        if default_target in cities:
            self.controls.set_target_city(default_target)
            self.graph_canvas.set_target_city(default_target)

    def _connect_signals(self) -> None:
        """
        Підписуємося на сигнали від ControlsPanel і GraphCanvas.
        """
        # --- з ControlsPanel ---
        self.controls.request_find_path.connect(self._on_find_path)
        self.controls.request_step.connect(self._on_step_visualization)
        self.controls.request_play.connect(self._on_play_visualization)
        self.controls.request_pause.connect(self._on_pause_visualization)
        self.controls.request_reset_visualization.connect(
            self._on_reset_visualization
        )
        self.controls.graph_changed.connect(self._on_graph_changed)
        self.controls.delay_changed.connect(self.graph_canvas.set_step_delay)

        # зміна початкової/кінцевої вершини – підсвічуємо на Canvas
        self.controls.source_city_changed.connect(
            self.graph_canvas.set_source_city
        )
        self.controls.target_city_changed.connect(
            self.graph_canvas.set_target_city
        )

        # зміна видимості карти
        self.controls.map_visibility_changed.connect(
            self.graph_canvas.set_show_map
        )

        # --- з GraphCanvas (клік по місту / мапі) ---
        self.graph_canvas.node_source_selected.connect(
            self.controls.set_source_city
        )
        self.graph_canvas.node_target_selected.connect(
            self.controls.set_target_city
        )
        self.graph_canvas.node_selected.connect(
            self.controls.set_selected_city_for_edit
        )
        self.graph_canvas.position_selected.connect(
            self.controls.set_new_city_position
        )

    # ----------- обробники сигналів -----------

    def _on_find_path(self, source: str, target: str) -> None:
        """
        Обчислює шлях, показує його текстом під графом,
        передає шлях і кроки в Canvas.
        """
        result = self._path_service.find_shortest_path(source, target)
        self._last_result = result
        if result is None or not result.path:
            self._set_result_text("Шлях не знайдено.")
            self.graph_canvas.clear_path_highlight()
            return

        text = self._format_path_result(result.path, result.total)
        self._set_result_text(text)

        # шлях завжди підсвічується після пошуку
        self.graph_canvas.set_path(result.path)
        # кроки – для візуалізації «Крок»/«Авто»
        self.graph_canvas.set_visualization_steps(result.steps)

    def _on_step_visualization(self) -> None:
        self.graph_canvas.show_next_step()

    def _on_play_visualization(self) -> None:
        self.graph_canvas.start_auto_play()

    def _on_pause_visualization(self) -> None:
        self.graph_canvas.pause_auto_play()

    def _on_reset_visualization(self) -> None:
        """
        «Скинути» – чистимо і візуалізацію, і знайдений шлях, і текст.
        """
        self.graph_canvas.reset_visualization()
        self._set_result_text("")

    def _on_graph_changed(self) -> None:
        """
        Викликається, коли користувач змінює граф.
        """
        self.graph_canvas.refresh()
        self.controls.update_cities(self._graph_service.list_cities())
        self.graph_canvas.reset_visualization()
        self._set_result_text("")

    # ----------- допоміжні методи для результату -----------

    def _set_result_text(self, text: str) -> None:
        self.result_view.setPlainText(text)

    def _format_time(self) -> str:
        """
        Форматує час виконання алгоритму з останнього результату.
        Повертає рядок типу '0.42 мс' або '1.234 с'.
        """
        result = getattr(self, "_last_result", None)
        if result is None:
            return "—"

        time_ms = getattr(result, "time_ms", None)
        if time_ms is None:
            return "—"

        # < 1 мс – показати з більшою точністю
        if time_ms < 1.0:
            return f"{time_ms:.3f} мс"
        # < 1000 мс – просто мілісекунди
        if time_ms < 1000.0:
            return f"{time_ms:.2f} мс"

        # >= 1 с – переводимо в секунди
        seconds = time_ms / 1000.0
        return f"{seconds:.3f} с"

    def _format_path_result(
        self, path: List[str], total: Optional[float]
    ) -> str:
        """
        Форматування результату в стилі:
        Ужгород (268 км) → Львів (127 км) → Тернопіль → ...
        + список сегментів і загальна довжина.
        """
        if not path:
            return "Шлях не знайдено."

        segments: List[str] = []
        arrow_parts: List[str] = []

        for i in range(len(path) - 1):
            a = path[i]
            b = path[i + 1]

            w = self._get_edge_weight(a, b)
            w_str = f"{w:.0f} км" if w is not None else "—"

            segments.append(f"{a} → {b}: {w_str}")
            arrow_parts.append(f"{a} ({w_str})")

        # останнє місто без довжини після нього
        arrow_parts.append(path[-1])

        total_str = f"{total:.0f} км" if total is not None else "—"

        pretty_arrow_line = " → ".join(arrow_parts)

        return (
            f"Найкоротший шлях: {total_str} (час: {self._format_time()})\n"
            f"{pretty_arrow_line}\n\n"
            f"Сегменти:\n  " + "\n  ".join(segments)
        )

    def _get_edge_weight(self, a: str, b: str) -> Optional[float]:
        """
        Повертає вагу ребра між a та b (якщо є).
        """
        adj = self._graph.adjacency
        if a in adj and b in adj[a]:
            return adj[a][b]
        if b in adj and a in adj[b]:
            return adj[b][a]
        return None
