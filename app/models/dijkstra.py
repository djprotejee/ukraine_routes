from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .graph import Graph


@dataclass
class Step:
    """
    Один крок візуалізації Дейкстри.
    - current      – поточна вершина, яку "витягнули" з черги;
    - neighbor     – сусід, до якого пробуємо релаксувати (може бути None);
    - new_distance – нова відстань, якщо релаксація вдала;
    - distances    – копія словника відстаней на цей момент;
    - visited      – множина вже остаточно оброблених вершин.
    """
    current: str
    neighbor: Optional[str]
    new_distance: Optional[float]
    distances: Dict[str, float]
    visited: List[str]


@dataclass
class DijkstraResult:
    """
    Результат роботи алгоритму:
    - distances   – відстань від source до кожної вершини;
    - previous    – попередник у найкоротшому шляху;
    - path        – відновлений шлях від source до target (якщо задано);
    - total       – сумарна довжина цього шляху (або None, якщо недосяжно);
    - steps       – кроки для візуалізації.
    """
    distances: Dict[str, float]
    previous: Dict[str, Optional[str]]
    path: List[str]
    total: Optional[float]
    steps: List[Step]


def _reconstruct_path(previous: Dict[str, Optional[str]],
                      source: str,
                      target: str) -> List[str]:
    """
    Відновлення шляху з мапи попередників.
    """
    path: List[str] = []
    current: Optional[str] = target

    while current is not None:
        path.append(current)
        if current == source:
            break
        current = previous.get(current)

    if not path or path[-1] != source:
        return []

    path.reverse()
    return path


def run_dijkstra(graph: Graph,
                 source: str,
                 target: Optional[str] = None) -> DijkstraResult:
    """
    Класична реалізація алгоритму Дейкстри з фіксацією кроків
    для графічної візуалізації.

    Використовує просту реалізацію через неефективний пошук
    мінімуму (O(V^2)), але цього достатньо для навчального проєкту.
    """
    vertices = list(graph.vertices.keys())
    if source not in vertices:
        raise ValueError(f"Початкова вершина '{source}' відсутня у графі")

    # Ініціалізація
    INF = float("inf")
    distances: Dict[str, float] = {v: INF for v in vertices}
    previous: Dict[str, Optional[str]] = {v: None for v in vertices}
    visited: List[str] = []

    distances[source] = 0.0

    steps: List[Step] = []

    while len(visited) < len(vertices):
        # Знаходимо невідвідану вершину з мінімальною відстанню
        current = None
        current_dist = INF
        for v in vertices:
            if v in visited:
                continue
            if distances[v] < current_dist:
                current_dist = distances[v]
                current = v

        if current is None:
            break  # решта вершин недосяжні

        visited.append(current)

        # Якщо маємо цільову вершину і дійшли до неї – можна зупинитись
        if target is not None and current == target:
            steps.append(
                Step(
                    current=current,
                    neighbor=None,
                    new_distance=None,
                    distances=dict(distances),
                    visited=list(visited),
                )
            )
            break

        # Релаксація сусідів
        for neighbor, weight in graph.neighbors(current).items():
            if neighbor in visited:
                continue

            alt = distances[current] + weight
            if alt < distances[neighbor]:
                distances[neighbor] = alt
                previous[neighbor] = current
                steps.append(
                    Step(
                        current=current,
                        neighbor=neighbor,
                        new_distance=alt,
                        distances=dict(distances),
                        visited=list(visited),
                    )
                )
            else:
                steps.append(
                    Step(
                        current=current,
                        neighbor=neighbor,
                        new_distance=None,
                        distances=dict(distances),
                        visited=list(visited),
                    )
                )

    # Відновлюємо шлях, якщо є target
    if target is not None:
        path = _reconstruct_path(previous, source, target)
        total = distances[target] if path else None
    else:
        path = []
        total = None

    return DijkstraResult(
        distances=distances,
        previous=previous,
        path=path,
        total=total,
        steps=steps,
    )
