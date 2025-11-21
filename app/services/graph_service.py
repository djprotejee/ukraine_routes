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

    def add_city(self, name: str, x: float, y: float) -> None:
        if not name:
            return
        self._graph.add_vertex(name, x, y)

    def remove_city(self, name: str) -> None:
        self._graph.remove_vertex(name)

    def set_city_position(self, name: str, x: float, y: float) -> None:
        self._graph.set_vertex_position(name, x, y)

    # ---------- ребра ----------

    def add_road(self, source: str, target: str, distance: float) -> None:
        if not source or not target or source == target:
            return
        self._graph.add_edge(source, target, distance)

    def remove_road(self, source: str, target: str) -> None:
        self._graph.remove_edge(source, target)
