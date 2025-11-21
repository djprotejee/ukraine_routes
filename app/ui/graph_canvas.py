from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPen, QBrush, QTransform, QFont, QColor
from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsTextItem,
)

from app.models import Graph
from app.models.dijkstra import Step


@dataclass
class NodeItems:
    """Графічні елементи однієї вершини."""
    circle: QGraphicsEllipseItem
    label: QGraphicsTextItem


@dataclass
class EdgeItems:
    """Графічні елементи одного ребра."""
    line: QGraphicsLineItem
    label: QGraphicsTextItem


class GraphCanvas(QGraphicsView):
    """
    Полотно з графом:
    - масштабування колесиком;
    - панорамування правою кнопкою;
    - перетягування вершин лівою кнопкою;
    - вибір міст (Shift/Ctrl/клік);
    - постійне підсвічування початкової/кінцевої вершин;
    - візуалізація кроків Дейкстри;
    - знайдений шлях видно після «Знайти шлях» і після завершення «Авто».
    """

    # Сигнали для MainWindow / ControlsPanel
    node_source_selected = Signal(str)          # Shift + клік по місту
    node_target_selected = Signal(str)          # Ctrl + клік по місту
    node_selected = Signal(str)                 # клік по місту без модифікаторів
    position_selected = Signal(float, float)    # клік по порожньому місцю (x, y у сцені)

    NODE_RADIUS = 14

    def __init__(self, graph: Graph, parent=None) -> None:
        super().__init__(parent)

        self._graph = graph
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # Початковий масштаб
        INITIAL_SCALE = 0.8
        self.scale(INITIAL_SCALE, INITIAL_SCALE)

        # Кроки Дейкстри
        self._step_delay_ms = 500
        self._steps: List[Step] = []
        self._current_step_index = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.show_next_step)

        # Графічні елементи
        self._node_items: Dict[str, NodeItems] = {}
        self._edge_items: Dict[str, EdgeItems] = {}

        # Стан панорамування
        self._panning = False
        self._pan_start = None

        # Стан drag вершини
        self._dragging_node_name: Optional[str] = None
        self._drag_moved: bool = False

        # Початкова та кінцева вершини
        self._source_city: Optional[str] = None
        self._target_city: Optional[str] = None

        # Поточний шлях (список міст) + прапорець, чи показувати його
        self._current_path: List[str] = []
        self._path_visible: bool = True  # для «Авто»: тимчасово ховаємо шлях

        # Налаштування вигляду
        self.setRenderHints(self.renderHints())
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

    # ---------- Загальне оновлення ----------

    def refresh(self) -> None:
        """Повне перемальовування графа з моделі Graph."""
        self._scene.clear()
        self._node_items.clear()
        self._edge_items.clear()

        # Спочатку ребра, потім вершини
        for edge in self._graph.edges:
            self._draw_edge(edge.source, edge.target, edge.weight)

        for name, vertex in self._graph.vertices.items():
            self._draw_vertex(name, vertex.x, vertex.y)

        self._scene.setSceneRect(self._scene.itemsBoundingRect())
        self._apply_all_coloring()

    # ---------- Шлях / кроки / джерело-ціль ----------

    def set_visualization_steps(self, steps: List[Step]) -> None:
        """
        Встановлює кроки Дейкстри для візуалізації.
        Path не чіпає.
        """
        self._steps = steps
        self._current_step_index = 0
        self._apply_all_coloring()

    def set_step_delay(self, ms: int) -> None:
        self._step_delay_ms = max(50, ms)
        if self._timer.isActive():
            self._timer.setInterval(self._step_delay_ms)

    def set_path(self, path: List[str]) -> None:
        """
        Запам'ятовує знайдений шлях і одразу підсвічує його.
        """
        self._current_path = path or []
        self._path_visible = True
        self._apply_all_coloring()

    def clear_path_highlight(self) -> None:
        """Очищає знайдений шлях і його підсвічування."""
        self._current_path = []
        self._apply_all_coloring()

    def set_source_city(self, name: str) -> None:
        """Встановлює початкову вершину (темно-зелена)."""
        self._source_city = name if name in self._graph.vertices else None
        self._apply_all_coloring()

    def set_target_city(self, name: str) -> None:
        """Встановлює кінцеву вершину (червона)."""
        self._target_city = name if name in self._graph.vertices else None
        self._apply_all_coloring()

    def show_next_step(self) -> None:
        """
        Показує наступний крок візуалізації.
        Якщо кроки закінчились – зупиняємо таймер і показуємо шлях (якщо є).
        """
        if not self._steps:
            self._timer.stop()
            # якщо шлях є, робимо його видимим
            if self._current_path:
                self._path_visible = True
                self._apply_all_coloring()
            return

        if self._current_step_index >= len(self._steps):
            self._timer.stop()
            if self._current_path:
                self._path_visible = True
                self._apply_all_coloring()
            return

        step = self._steps[self._current_step_index]
        self._current_step_index += 1

        self._apply_step_visual(step)

    def start_auto_play(self) -> None:
        """
        Запускає авто-візуалізацію:
        - спочатку показує тільки процес (шлях ховаємо),
        - після завершення показує знайдений шлях.
        """
        if not self._steps:
            return
        self._current_step_index = 0
        self._path_visible = False  # тимчасово ховаємо шлях
        self._apply_all_coloring()

        self._timer.setInterval(self._step_delay_ms)
        self._timer.start()

    def pause_auto_play(self) -> None:
        self._timer.stop()

    def reset_visualization(self) -> None:
        """
        «Скинути»:
        - зупиняє таймер;
        - очищає кроки;
        - очищає шлях;
        - залишає тільки базове розфарбування + source/target.
        """
        self._timer.stop()
        self._current_step_index = 0
        self._steps = []
        self._current_path = []
        self._path_visible = True
        self._apply_all_coloring()

    # ---------- Малювання вершин/ребер ----------

    def _draw_vertex(self, name: str, x: float, y: float) -> None:
        r = self.NODE_RADIUS
        circle = self._scene.addEllipse(
            x - r,
            y - r,
            2 * r,
            2 * r,
            QPen(Qt.white),
            QBrush(Qt.darkCyan),
        )

        label = self._scene.addText(name)
        font = QFont()
        font.setPointSize(12)
        label.setFont(font)
        label.setDefaultTextColor(Qt.white)
        label.setPos(x + r + 2, y - r / 2)

        self._node_items[name] = NodeItems(circle=circle, label=label)

    def _draw_edge(self, source: str, target: str, weight: float) -> None:
        v1 = self._graph.vertices[source]
        v2 = self._graph.vertices[target]

        line = self._scene.addLine(
            v1.x,
            v1.y,
            v2.x,
            v2.y,
            QPen(Qt.gray),
        )

        mid_x = (v1.x + v2.x) / 2
        mid_y = (v1.y + v2.y) / 2
        label = self._scene.addText(f"{weight:.0f}")
        font = QFont()
        font.setPointSize(12)
        label.setFont(font)
        label.setDefaultTextColor(Qt.lightGray)
        label.setPos(mid_x, mid_y)

        key = f"{source}->{target}"
        self._edge_items[key] = EdgeItems(line=line, label=label)

    # ---------- Кольори / стилі ----------

    def _set_base_colors(self) -> None:
        """Базова розмальовка без шляху і без кроків."""
        for node in self._node_items.values():
            node.circle.setBrush(QBrush(Qt.darkCyan))
            node.circle.setPen(QPen(Qt.white, 1))

        for edge in self._edge_items.values():
            pen = QPen(Qt.gray, 1)
            edge.line.setPen(pen)
            edge.label.setDefaultTextColor(Qt.lightGray)

    def _apply_path_highlight(self) -> None:
        """Підсвічує знайдений шлях (якщо path_visible = True)."""
        if not self._path_visible or not self._current_path:
            return

        # вершини шляху (крім source/target)
        for name in self._current_path:
            if name in (self._source_city, self._target_city):
                continue
            node = self._node_items.get(name)
            if node:
                node.circle.setBrush(QBrush(Qt.green))

        # ребра шляху – товстіші й зелені
        for i in range(len(self._current_path) - 1):
            a = self._current_path[i]
            b = self._current_path[i + 1]
            key1 = f"{a}->{b}"
            key2 = f"{b}->{a}"
            edge = self._edge_items.get(key1) or self._edge_items.get(key2)
            if edge:
                pen = edge.line.pen()
                pen.setWidth(3)
                pen.setColor(Qt.green)
                edge.line.setPen(pen)

    def _apply_source_target_markers(self) -> None:
        """Підсвічує source/target поверх усього."""
        dark_green = QColor("#1b5e20")

        if self._source_city and self._source_city in self._node_items:
            node = self._node_items[self._source_city]
            node.circle.setBrush(QBrush(dark_green))

        if self._target_city and self._target_city in self._node_items:
            node = self._node_items[self._target_city]
            node.circle.setBrush(QBrush(Qt.red))

    def _apply_all_coloring(self) -> None:
        """
        Повністю оновлює кольори:
        1) базові;
        2) шлях (якщо path_visible=True);
        3) початкова/кінцева вершина.
        """
        self._set_base_colors()
        self._apply_path_highlight()
        self._apply_source_target_markers()

    def _apply_step_visual(self, step: Step) -> None:
        """
        Накладає крок візуалізації на поточну розмальовку.
        Використовується і для «Крок», і для «Авто».
        """
        # 1) база + (можливо) шлях + source/target
        self._apply_all_coloring()

        # 2) зверху – крок Дейкстри
        for name in step.visited:
            node = self._node_items.get(name)
            if node:
                node.circle.setBrush(QBrush(Qt.blue))

        current_node = self._node_items.get(step.current)
        if current_node:
            current_node.circle.setBrush(QBrush(Qt.yellow))

        if step.neighbor:
            node = self._node_items.get(step.neighbor)
            if node:
                node.circle.setBrush(QBrush(Qt.red))

            key1 = f"{step.current}->{step.neighbor}"
            key2 = f"{step.neighbor}->{step.current}"
            edge = self._edge_items.get(key1) or self._edge_items.get(key2)
            if edge:
                pen = edge.line.pen()
                pen.setWidth(3)
                pen.setColor(Qt.red)
                edge.line.setPen(pen)

        # 3) ще раз поверх – source/target, щоб не "перебити" їх кольори
        self._apply_source_target_markers()

    # ---------- Зум, панорамування, drag вершин, вибір ----------

    def wheelEvent(self, event):  # noqa: N802
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.RightButton:
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            return

        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            item = self._scene.itemAt(scene_pos, QTransform())

            clicked_city: Optional[str] = None
            if item is not None:
                for name, node in self._node_items.items():
                    if item is node.circle or item is node.label:
                        clicked_city = name
                        break

            if clicked_city is not None:
                # готуємось до drag вершини
                self._dragging_node_name = clicked_city
                self._drag_moved = False
            else:
                # клік по порожньому місцю – координата для нового міста
                self.position_selected.emit(scene_pos.x(), scene_pos.y())
                self._dragging_node_name = None
                self._drag_moved = False

            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):  # noqa: N802
        # панорамування правою кнопкою
        if self._panning and self._pan_start is not None:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.translate(delta.x() * -1, delta.y() * -1)
            return

        # drag вершини лівою кнопкою
        if (event.buttons() & Qt.LeftButton) and self._dragging_node_name:
            self._drag_moved = True
            name = self._dragging_node_name
            if name not in self._node_items or name not in self._graph.vertices:
                return

            scene_pos = self.mapToScene(event.pos())
            v = self._graph.vertices[name]
            v.x = scene_pos.x()
            v.y = scene_pos.y()

            # оновлюємо коло
            r = self.NODE_RADIUS
            items = self._node_items[name]
            items.circle.setRect(
                v.x - r,
                v.y - r,
                2 * r,
                2 * r,
            )
            # оновлюємо підпис вершини
            items.label.setPos(v.x + r + 2, v.y - r / 2)

            # оновлюємо всі ребра, де ця вершина
            for key, edge_item in self._edge_items.items():
                src, tgt = key.split("->", maxsplit=1)
                if src not in self._graph.vertices or tgt not in self._graph.vertices:
                    continue
                v1 = self._graph.vertices[src]
                v2 = self._graph.vertices[tgt]
                edge_item.line.setLine(v1.x, v1.y, v2.x, v2.y)
                mid_x = (v1.x + v2.x) / 2
                mid_y = (v1.y + v2.y) / 2
                edge_item.label.setPos(mid_x, mid_y)

            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):  # noqa: N802
        if event.button() == Qt.RightButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            return

        if event.button() == Qt.LeftButton and self._dragging_node_name:
            name = self._dragging_node_name
            moved = self._drag_moved
            self._dragging_node_name = None
            self._drag_moved = False

            # якщо не тягнули – трактуємо як клік по місту
            if not moved:
                modifiers = event.modifiers()
                if modifiers & Qt.ShiftModifier:
                    self.node_source_selected.emit(name)
                elif modifiers & Qt.ControlModifier:
                    self.node_target_selected.emit(name)
                else:
                    self.node_selected.emit(name)

            return

        super().mouseReleaseEvent(event)
