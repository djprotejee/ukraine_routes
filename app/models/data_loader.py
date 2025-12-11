from __future__ import annotations

import csv
import json
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any

from .graph import Graph


# ------------------ Афінна трансформація lat/lon → x/y ------------------

def _solve_affine_transform(pts_latlon, pts_xy):
    """
    Обчислює афінну матрицю A (2×3), яка переводить:
       [x]   [a b c] [lon]
       [y] = [d e f] [lat]
                     1
    pts_latlon – список (lon, lat)
    pts_xy     – список (x, y)
    """

    A = []
    B = []

    for (lon, lat), (x, y) in zip(pts_latlon, pts_xy):
        A.append([lon, lat, 1, 0, 0, 0])
        A.append([0, 0, 0, lon, lat, 1])
        B.append(x)
        B.append(y)

    A = np.array(A, dtype=float)
    B = np.array(B, dtype=float)

    # Розв'язуємо A * params = B
    params, *_ = np.linalg.lstsq(A, B, rcond=None)

    # params = [a, b, c, d, e, f]
    return params.reshape(2, 3)


def _apply_affine(matrix, lon, lat):
    """Повертає (x, y) після афінного перетворення."""
    x = matrix[0, 0] * lon + matrix[0, 1] * lat + matrix[0, 2]
    y = matrix[1, 0] * lon + matrix[1, 1] * lat + matrix[1, 2]
    return float(x), float(y)


# ------------------ Завантаження координат ------------------

def _load_positions(data_dir: Path) -> Dict[str, Dict[str, float]]:
    """
    Читає cities_positions.json та повертає вже готові x/y,
    використавши афінне перетворення, щоб координати точно
    збігалися з картою (781×603).
    """
    path = data_dir / "cities_positions.json"
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    # Контрольні точки (піксельні координати реальної карти 1066×802)
    reference = {
        "Київ": (502, 197),
        "Львів": (136, 234),
        "Донецьк": (926, 412),
        "Сімферополь": (720, 720),
        "Маріуполь": (920, 499),
        "Луганськ": (1009, 348),
        "Чернігів": (542, 96),
        "Одеса": (510, 578),
        "Луцьк": (217, 152),
    }

    pts_latlon = []
    pts_xy = []

    for city, (x, y) in reference.items():
        if city not in raw:
            continue
        lat = float(raw[city]["lat"])
        lon = float(raw[city]["lon"])
        pts_latlon.append((lon, lat))
        pts_xy.append((x, y))

    # Обчислюємо афінну матрицю
    affine = _solve_affine_transform(pts_latlon, pts_xy)

    # Перетворюємо всі міста
    result = {}
    for city, v in raw.items():
        lat = float(v["lat"])
        lon = float(v["lon"])
        x, y = _apply_affine(affine, lon, lat)
        result[city] = {"x": x, "y": y}

    return result


# ------------------ Завантаження графа ------------------

def load_graph(data_dir: Optional[Path] = None) -> Graph:
    if data_dir is None:
        data_dir = Path(__file__).resolve().parents[2] / "data"

    graph = Graph()

    positions = _load_positions(data_dir)

    distances_path = data_dir / "distances.csv"
    with distances_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            a = row["source"].strip()
            b = row["target"].strip()
            w = float(row["distance_km"])

            for city in (a, b):
                if city not in graph.vertices:
                    pos = positions.get(city, {"x": 0.0, "y": 0.0})
                    graph.add_vertex(city, pos["x"], pos["y"])

            graph.add_edge(a, b, w)

    return graph
