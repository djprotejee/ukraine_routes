from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class Vertex:
    """
    Вершина графа.
    name  – назва міста.
    x, y  – координати для візуалізації (умовна карта).
    """
    name: str
    x: float
    y: float


@dataclass
class Edge:
    """
    Неорієнтоване ребро між двома вершинами.
    weight – відстань у кілометрах.
    """
    source: str
    target: str
    weight: float


class Graph:
    """
    Проста реалізація неорієнтованого зваженого графа.
    Зберігаємо:
    - словник вершин;
    - список ребер;
    - матрицю суміжності у вигляді словника словників.
    """

    def __init__(self) -> None:
        self._vertices: Dict[str, Vertex] = {}
        self._edges: List[Edge] = []
        self._adjacency: Dict[str, Dict[str, float]] = {}

    # ----------------- базові методи -----------------

    @property
    def vertices(self) -> Dict[str, Vertex]:
        return self._vertices

    @property
    def edges(self) -> List[Edge]:
        return self._edges

    @property
    def adjacency(self) -> Dict[str, Dict[str, float]]:
        return self._adjacency

    def add_vertex(self, name: str, x: float = 0.0, y: float = 0.0) -> None:
        """
        Додає вершину, якщо її ще немає.
        """
        if name in self._vertices:
            return

        self._vertices[name] = Vertex(name=name, x=x, y=y)
        self._adjacency.setdefault(name, {})

    def remove_vertex(self, name: str) -> None:
        """
        Видаляє вершину та всі пов'язані з нею ребра.
        """
        if name not in self._vertices:
            return

        # Видалити ребра зі списку
        self._edges = [e for e in self._edges if e.source != name and e.target != name]

        # Видалити зі словника суміжності
        self._adjacency.pop(name, None)
        for nbrs in self._adjacency.values():
            nbrs.pop(name, None)

        # Видалити саму вершину
        self._vertices.pop(name, None)

    def add_edge(self, source: str, target: str, weight: float) -> None:
        """
        Додає неорієнтоване ребро.
        Якщо вершини не існують – створюємо їх у координатах (0,0).
        """
        if source == target:
            return

        if source not in self._vertices:
            self.add_vertex(source)
        if target not in self._vertices:
            self.add_vertex(target)

        # Запис у список ребер
        self._edges.append(Edge(source=source, target=target, weight=weight))

        # Запис у матрицю суміжності
        self._adjacency.setdefault(source, {})[target] = weight
        self._adjacency.setdefault(target, {})[source] = weight

    def remove_edge(self, source: str, target: str) -> None:
        """
        Видаляє ребро між source та target, якщо воно є.
        """
        self._edges = [
            e
            for e in self._edges
            if not (
                (e.source == source and e.target == target)
                or (e.source == target and e.target == source)
            )
        ]

        if source in self._adjacency:
            self._adjacency[source].pop(target, None)
        if target in self._adjacency:
            self._adjacency[target].pop(source, None)

    # ----------------- допоміжні методи -----------------

    def neighbors(self, name: str) -> Dict[str, float]:
        """
        Повертає словник {сусід: вага} для заданої вершини.
        """
        return self._adjacency.get(name, {})

    def get_vertex_position(self, name: str) -> Tuple[float, float]:
        v = self._vertices[name]
        return v.x, v.y

    def set_vertex_position(self, name: str, x: float, y: float) -> None:
        if name not in self._vertices:
            self.add_vertex(name, x, y)
        else:
            v = self._vertices[name]
            v.x = x
            v.y = y
