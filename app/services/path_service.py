from __future__ import annotations

import time
from typing import Optional

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

        # вимірюємо час
        t_start = time.perf_counter()

        if source == target:
            result = run_dijkstra(self._graph, source, target)
            result.path = [source]
            result.total = 0.0
        else:
            result = run_dijkstra(self._graph, source, target)

        t_end = time.perf_counter()

        # додаємо нове поле до результату
        result.time_ms = (t_end - t_start) * 1000.0  # час у мілісекундах

        return result
