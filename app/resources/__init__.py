from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication


def load_dark_theme(app: QApplication, qss_path: Optional[Path] = None) -> None:
    """
    Завантажує темну тему з файлу QSS.
    Якщо файл відсутній – тихо нічого не робимо.
    """
    if qss_path is None:
        qss_path = Path(__file__).resolve().parent / "dark_theme.qss"

    if not qss_path.exists():
        return

    with qss_path.open("r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())
