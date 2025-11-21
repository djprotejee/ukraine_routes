from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Optional

from .graph import Graph


def load_graph(data_dir: Optional[Path] = None) -> Graph:
    """
    Завантажує граф з:
    - distances.csv   – ребра;
    - cities_positions_verbose.json – координати вершин.

    Якщо координат для деякого міста немає, воно отримує (0, 0).
    """
    if data_dir is None:
        # data/ відносно app/
        data_dir = Path(__file__).resolve().parents[2] / "data"

    graph = Graph()

    # Спочатку читаємо позиції міст
    positions_path = data_dir / "cities_positions_verbose.json"
    positions = {}
    if positions_path.exists():
        with positions_path.open("r", encoding="utf-8") as f:
            positions = json.load(f)

    # Читаємо ребра та створюємо вершини
    distances_path = data_dir / "distances.csv"
    with distances_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            source = row["source"].strip()
            target = row["target"].strip()
            weight = float(row["distance_km"])

            # Координати, якщо є
            for city in (source, target):
                if city not in graph.vertices:
                    pos = positions.get(city, {"x": 0.0, "y": 0.0})
                    graph.add_vertex(city, x=float(pos["x"]), y=float(pos["y"]))

            graph.add_edge(source, target, weight)

    return graph
