from __future__ import annotations

from typing import List

from app.models import Graph


class GraphService:
    """
    Сервіс роботи з графом.
    Інкапсулює базові операції додавання/видалення вершин та ребер
    для використання з GUI.
    """

    def __init__(self, graph: Graph) -> None:
        self._graph = graph

    @property
    def graph(self) -> Graph:
        return self._graph

    # ---------- вершини ----------

    def list_cities(self) -> List[str]:
        return sorted(self._graph.vertices.keys())

    def has_city(self, name: str) -> bool:
        return name in self._graph.vertices

    def add_city(self, name: str, x: float, y: float) -> None:
        if not name:
            return
        if self.has_city(name):
            # UI покаже помилку, тут просто не дублюємо
            return
        self._graph.add_vertex(name, x, y)

    def remove_city(self, name: str) -> None:
        self._graph.remove_vertex(name)

    def set_city_position(self, name: str, x: float, y: float) -> None:
        self._graph.set_vertex_position(name, x, y)

    # ---------- ребра ----------

    def has_arc(self, source: str, target: str) -> bool:
        """Чи існує дуга source -> target."""
        return (
            source in self._graph.adjacency
            and target in self._graph.adjacency[source]
        )

    def has_road(self, a: str, b: str) -> bool:
        """
        Чи існує "дорога" між містами a та b – в будь-якому напрямку.
        """
        return self.has_arc(a, b) or self.has_arc(b, a)

    def add_road(self, source: str, target: str, distance: float) -> None:
        """
        Додає дорогу (за замовчуванням двосторонню).
        """
        if not source or not target or source == target:
            return
        if self.has_road(source, target):
            # UI скаже "така дорога вже існує"
            return
        self._graph.add_undirected_edge(source, target, distance)

    def remove_road(
        self,
        source: str,
        target: str,
        *,
        arc_only: bool = False,
    ) -> None:
        """
        Якщо arc_only=True – видаляємо лише дугу source -> target.
        Якщо False – прибираємо дорогу повністю в обидва боки.
        """
        if arc_only:
            self._graph.remove_directed_edge(source, target)
        else:
            self._graph.remove_undirected_edge(source, target)
