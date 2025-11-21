import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from app.ui.main_window import MainWindow
from app.resources import load_dark_theme


def main() -> None:
    """
    Точка входу в застосунок.
    Відповідає тільки за:
    - створення QApplication;
    - завантаження стилю;
    - показ головного вікна.
    """
    app = QApplication(sys.argv)

    # Темна тема (через QSS)
    load_dark_theme(app)

    # Опціонально: встановити іконку додатку, якщо додаси файл
    icon_path = Path(__file__).resolve().parent / "resources" / "icons" / "play.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
