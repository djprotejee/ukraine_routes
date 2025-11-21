from __future__ import annotations

from typing import List, Optional

from app.models import Graph, DijkstraResult, run_dijkstra


class PathService:
    """
    Сервіс пошуку найкоротшого шляху.
    Обгортає виклик алгоритму Дейкстри та додаткову бізнес-логіку,
    потрібну для GUI.
    """

    def __init__(self, graph: Graph) -> None:
        self._graph = graph

    def find_shortest_path(
        self, source: str, target: str
    ) -> Optional[DijkstraResult]:
        if source not in self._graph.vertices or target not in self._graph.vertices:
            return None
        if source == target:
            # тривіальний шлях – одна вершина з нульовою довжиною
            result = run_dijkstra(self._graph, source, target)
            result.path = [source]
            result.total = 0.0
            return result

        return run_dijkstra(self._graph, source, target)
