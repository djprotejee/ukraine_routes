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
    Ребро між двома вершинами.
    weight – відстань у кілометрах.
    Тут трактуємо Edge як ОРІЄНТОВАНЕ ребро source -> target.
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

    def add_directed_edge(self, source: str, target: str, weight: float) -> None:
        """
        Додає ОРІЄНТОВАНЕ ребро source -> target.
        Якщо вершини не існують – створюємо їх у координатах (0,0).
        """
        if source == target:
            return

        if source not in self._vertices:
            self.add_vertex(source)
        if target not in self._vertices:
            self.add_vertex(target)

        # Запис у список орієнтованих ребер
        self._edges.append(Edge(source=source, target=target, weight=weight))

        # Запис у матрицю суміжності тільки в один бік
        self._adjacency.setdefault(source, {})[target] = weight

    def add_undirected_edge(self, source: str, target: str, weight: float) -> None:
        """
        Додає НЕорієнтовану дорогу (тобто дві дуги: source->target і target->source).
        """
        self.add_directed_edge(source, target, weight)
        self.add_directed_edge(target, source, weight)

    # для зворотної сумісності – стара назва лишається як "дорога в обидва боки"
    def add_edge(self, source: str, target: str, weight: float) -> None:
        self.add_undirected_edge(source, target, weight)

    def remove_directed_edge(self, source: str, target: str) -> None:
        """
        Видаляє тільки дугу source -> target.
        """
        self._edges = [
            e for e in self._edges
            if not (e.source == source and e.target == target)
        ]
        if source in self._adjacency:
            self._adjacency[source].pop(target, None)

    def remove_undirected_edge(self, source: str, target: str) -> None:
        """
        Видаляє дорогу повністю – обидві дуги (source->target і target->source).
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

    # зворотна сумісність
    def remove_edge(self, source: str, target: str) -> None:
        self.remove_undirected_edge(source, target)

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
