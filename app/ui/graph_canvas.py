from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPen, QBrush, QTransform, QFont, QColor, QPixmap
from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsTextItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
)

from app.models import Graph
from app.models.dijkstra import Step


@dataclass
class NodeItems:
    """Графічні елементи однієї вершини."""
    circle: QGraphicsEllipseItem
    label: QGraphicsTextItem
    label_bg: QGraphicsRectItem


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
    - знайдений шлях видно після «Знайти шлях» і після завершення «Авто»;
    - фонове зображення карти України (опційно).
    """

    # Палітра для графу
    COLOR_NODE_BASE = QColor("#1565c0")  # синій вузол
    COLOR_NODE_BORDER = QColor("#ffffff")  # біла обводка
    COLOR_NODE_LABEL = QColor("#0d0d0d")  # темний текст

    COLOR_EDGE_BASE = QColor(0, 0, 0, 130)  # напівпрозорі чорні ребра
    COLOR_EDGE_LABEL = QColor("#37474f")  # темно сірий текст ваги

    COLOR_PATH_NODE = QColor("#73e600")  # бірюзові вузли шляху
    COLOR_PATH_EDGE = QColor("#ff6d00")  # помаранчеві ребра шляху

    COLOR_SOURCE = QColor("#2e7d32")  # зелений старт
    COLOR_TARGET = QColor("#c62828")  # червоний фініш

    COLOR_VISITED = QColor("#cc33ff")  # сині відвідані
    COLOR_CURRENT = QColor("#ffeb3b")  # жовтий поточний
    COLOR_NEIGHBOR = QColor("#e53935")  # червоний сусід

    # Сигнали для MainWindow / ControlsPanel
    node_source_selected = Signal(str)          # Shift + клік по місту
    node_target_selected = Signal(str)          # Ctrl + клік по місту
    node_selected = Signal(str)                 # клік по місту без модифікаторів
    position_selected = Signal(float, float)    # клік по порожньому місцю (x, y у сцені)

    NODE_RADIUS = 20

    def __init__(self, graph: Graph, parent=None) -> None:
        super().__init__(parent)

        self._graph = graph
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # Початковий масштаб
        INITIAL_SCALE = 1
        self.scale(INITIAL_SCALE, INITIAL_SCALE)

        # Кроки Дейкстри
        self._step_delay_ms = 300
        self._steps: List[Step] = []
        self._current_step_index = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.show_next_step)

        # Графічні елементи
        self._node_items: Dict[str, NodeItems] = {}
        self._edge_items: Dict[str, EdgeItems] = {}

        # Фонова карта
        self._show_map: bool = True
        self._map_item: Optional[QGraphicsPixmapItem] = None
        self._map_pixmap: Optional[QPixmap] = None

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

    # ---------- Публічне керування картою ----------

    def set_show_map(self, show: bool) -> None:
        """
        Вмикає / вимикає відображення фонової карти.
        Викликати, наприклад, з чекбоксу в панелі керування.
        """
        self._show_map = bool(show)
        self.refresh()

    # ---------- Завантаження та додавання карти ----------

    def _load_map_pixmap(self) -> Optional[QPixmap]:
        """Пробує знайти карту України в папці data/."""
        if self._map_pixmap is not None:
            return self._map_pixmap

        data_dir = Path(__file__).resolve().parents[1] / "resources" / "images"
        candidates = [
            "ukraine-map.jpg",
            "ukraine-map.png",
            "ukraine_map.jpg",
            "ukraine_map.png",
        ]

        for name in candidates:
            path = data_dir / name
            if path.exists():
                pixmap = QPixmap(str(path))
                if not pixmap.isNull():
                    self._map_pixmap = pixmap
                    return pixmap

        # Якщо не знайшли файл – просто працюємо без карти
        self._map_pixmap = None
        return None

    def _add_background_map(self) -> None:
        """
        Додає на сцену фонову карту 1:1 у тих же координатах,
        що й вершини (x/y з data_loader уже в пікселях 781×603).
        """
        if not self._show_map:
            return

        pixmap = self._load_map_pixmap()
        if pixmap is None or pixmap.isNull():
            return

        item = self._scene.addPixmap(pixmap)
        item.setZValue(-100)

        # Сцена від 0,0 до розміру картинки
        self._scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())

        self._map_item = item

    # ---------- Загальне оновлення ----------

    def refresh(self) -> None:
        """Повне перемальовування графа з моделі Graph."""
        self._scene.clear()
        self._node_items.clear()
        self._edge_items.clear()
        self._map_item = None

        # Спочатку додаємо карту, потім ребра й вершини
        self._add_background_map()

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
        Якщо кроки закінчились – зупиняємо таймер і показуємо шлях (якщо є),
        причому вершини шляху – зелені, а інші відвідані – фіолетові.
        """
        if not self._steps:
            self._timer.stop()
            if self._current_path:
                self._path_visible = True
                self._apply_all_coloring()
            return

        if self._current_step_index >= len(self._steps):
            # усе вже показали – фінальний стан
            self._timer.stop()

            # показуємо шлях, якщо є
            if self._current_path:
                self._path_visible = True

            # база + шлях + source/target
            self._apply_all_coloring()

            # поверх цього – visited, але тільки ті,
            # які НЕ входять у шлях і не є source/target
            last_step = self._steps[-1]
            for name in last_step.visited:
                if name in (self._source_city, self._target_city):
                    continue
                if self._current_path and name in self._current_path:
                    continue  # вузли шляху лишаємо зеленими

                node = self._node_items.get(name)
                if node:
                    node.circle.setBrush(QBrush(self.COLOR_VISITED))

            # ще раз поверх – source/target, щоб їх колір не перебити
            self._apply_source_target_markers()
            return

        # звичайний крок анімації
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

        # Коло вузла
        circle = self._scene.addEllipse(
            x - r,
            y - r,
            2 * r,
            2 * r,
            QPen(self.COLOR_NODE_BORDER, 2),
            QBrush(self.COLOR_NODE_BASE),
        )

        # Текст
        label = self._scene.addText(name)
        font = QFont()
        font.setPointSize(7)  # менший шрифт
        font.setBold(True)
        label.setFont(font)
        label.setDefaultTextColor(self.COLOR_NODE_LABEL)
        label.setPos(0, 0)  # тимчасово, щоб взяти boundingRect

        br = label.boundingRect()
        padding = 1.5  # менший відступ

        # розмір плашки: за замовчуванням менша, але якщо текст широкий — може вилізти за коло
        w = br.width() + 2 * padding
        h = br.height() + 2 * padding

        bg_rect = self._scene.addRect(
            x - w / 2,
            y - h / 2,
            w,
            h,
            QPen(QColor("#212121"), 1.2),
            QBrush(QColor(255, 249, 196, 230)),  # світло-жовта, трохи прозора
        )

        # центруємо текст у плашці / колі
        label.setPos(
            x - br.width() / 2,
            y - br.height() / 2,
        )

        circle.setZValue(0)
        bg_rect.setZValue(1)
        label.setZValue(2)

        self._node_items[name] = NodeItems(
            circle=circle,
            label=label,
            label_bg=bg_rect,
        )

    def _draw_edge(self, source: str, target: str, weight: float) -> None:
        v1 = self._graph.vertices[source]
        v2 = self._graph.vertices[target]

        line = self._scene.addLine(
            v1.x,
            v1.y,
            v2.x,
            v2.y,
            QPen(self.COLOR_EDGE_BASE, 1.6),
        )

        mid_x = (v1.x + v2.x) / 2
        mid_y = (v1.y + v2.y) / 2
        label = self._scene.addText(f"{weight:.0f}")
        font = QFont()
        font.setPointSize(12)
        label.setFont(font)
        label.setDefaultTextColor(self.COLOR_EDGE_LABEL)
        label.setPos(mid_x, mid_y)

        key = f"{source}->{target}"
        self._edge_items[key] = EdgeItems(line=line, label=label)

    # ---------- Кольори / стилі ----------

    def _set_base_colors(self) -> None:
        """Базова розмальовка без шляху і без кроків."""
        for node in self._node_items.values():
            node.circle.setBrush(QBrush(self.COLOR_NODE_BASE))
            node.circle.setPen(QPen(self.COLOR_NODE_BORDER, 2))

        for edge in self._edge_items.values():
            pen = QPen(self.COLOR_EDGE_BASE, 1.6)
            edge.line.setPen(pen)
            edge.label.setDefaultTextColor(self.COLOR_EDGE_LABEL)

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
                node.circle.setBrush(QBrush(self.COLOR_PATH_NODE))

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
                pen.setColor(self.COLOR_PATH_EDGE)
                edge.line.setPen(pen)

    def _apply_source_target_markers(self) -> None:
        """Підсвічує source/target поверх усього."""

        if self._source_city and self._source_city in self._node_items:
            node = self._node_items[self._source_city]
            node.circle.setBrush(QBrush(self.COLOR_SOURCE))

        if self._target_city and self._target_city in self._node_items:
            node = self._node_items[self._target_city]
            node.circle.setBrush(QBrush(self.COLOR_TARGET))

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
        Порядок:
        1) база;
        2) visited (крім вершин шляху, щоб не бити зелений);
        3) шлях (якщо показуємо);
        4) current / neighbor;
        5) source / target.
        """
        # 1) база
        self._set_base_colors()

        # 2) visited, але НЕ вершини шляху (якщо шлях видимий)
        for name in step.visited:
            node = self._node_items.get(name)
            if not node:
                continue
            if self._path_visible and name in self._current_path:
                # цю вершину потім пофарбує _apply_path_highlight()
                continue
            node.circle.setBrush(QBrush(self.COLOR_VISITED))

        # 3) шлях (зелений), якщо його зараз показуємо
        if self._path_visible:
            self._apply_path_highlight()

        # 4) поточна вершина
        current_node = self._node_items.get(step.current)
        if current_node:
            current_node.circle.setBrush(QBrush(self.COLOR_CURRENT))

        # 4.1) сусід + ребро до нього
        if step.neighbor:
            neighbor_node = self._node_items.get(step.neighbor)
            if neighbor_node:
                neighbor_node.circle.setBrush(QBrush(self.COLOR_NEIGHBOR))

            key1 = f"{step.current}->{step.neighbor}"
            key2 = f"{step.neighbor}->{step.current}"
            edge = self._edge_items.get(key1) or self._edge_items.get(key2)
            if edge:
                pen = edge.line.pen()
                pen.setWidth(3)
                pen.setColor(self.COLOR_NEIGHBOR)
                edge.line.setPen(pen)

        # 5) source / target поверх усього
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
                    if item in (node.circle, node.label, node.label_bg):
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

            r = self.NODE_RADIUS
            items = self._node_items[name]

            # коло
            items.circle.setRect(
                v.x - r,
                v.y - r,
                2 * r,
                2 * r,
            )

            # текст + плашка по центру вузла
            br = items.label.boundingRect()
            padding = 1.5  # такий самий як у _draw_vertex

            items.label_bg.setRect(
                v.x - br.width() / 2 - padding,
                v.y - br.height() / 2 - padding,
                br.width() + 2 * padding,
                br.height() + 2 * padding,
            )

            items.label.setPos(
                v.x - br.width() / 2,
                v.y - br.height() / 2,
            )

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
