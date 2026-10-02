"""Application entry point."""
import sys
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database.database import init_database  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402
from ui.theme import GLOBAL_STYLESHEET  # noqa: E402

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def _load_thai_font(app: QApplication) -> None:
    font_dir = ASSETS_DIR / "fonts"
    if not font_dir.is_dir():
        return
    family = None
    for font_file in font_dir.glob("*.ttf"):
        font_id = QFontDatabase.addApplicationFont(str(font_file))
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            family = families[0]
    if family:
        app.setFont(QFont(family, 12))


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("StockApp")
    app.setOrganizationName("StockApp")
    _load_thai_font(app)
    app.setStyleSheet(GLOBAL_STYLESHEET)

    init_database()

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
