"""Visual theme: navy-gold classic government palette.

Single source of truth for colors so the sidebar (main_window.py) and the
rest of the app (via GLOBAL_STYLESHEET, applied once in main.py) stay
consistent. Printed documents (services/print_service.py) intentionally stay
plain black-on-white regardless of this theme, matching how official forms
are usually photocopied/scanned in government offices.
"""

NAVY = "#0b3d63"
NAVY_DARK = "#082c49"
NAVY_LIGHT = "#154d78"
GOLD = "#c9a227"
GOLD_DARK = "#a8841c"
GOLD_LIGHT = "#f1e4b8"
CREAM = "#f7f5f0"
CREAM_DARK = "#ece5d3"
WHITE = "#ffffff"
TEXT_DARK = "#22252a"
TEXT_MUTED = "#6b6558"
BORDER = "#d8d2be"
DANGER = "#a4231d"
SUCCESS = "#1f6b3a"
WARNING = "#a8641c"

GLOBAL_STYLESHEET = f"""
QWidget {{
    background-color: {CREAM};
    color: {TEXT_DARK};
}}
QMainWindow {{
    background-color: {CREAM};
}}
QLabel {{
    background: transparent;
}}
QPushButton {{
    background-color: {WHITE};
    color: {TEXT_DARK};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 6px 14px;
}}
QPushButton:hover {{
    background-color: {CREAM_DARK};
}}
QPushButton:pressed {{
    background-color: {GOLD_LIGHT};
}}
QPushButton:disabled {{
    color: {TEXT_MUTED};
    background-color: {CREAM_DARK};
}}
QPushButton:default {{
    background-color: {NAVY};
    color: {WHITE};
    border: 1px solid {NAVY_DARK};
    font-weight: 600;
}}
QPushButton:default:hover {{
    background-color: {NAVY_LIGHT};
}}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
    background-color: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px 8px;
    selection-background-color: {GOLD_LIGHT};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
    border: 1px solid {GOLD_DARK};
}}
QTableWidget {{
    background-color: {WHITE};
    alternate-background-color: {CREAM};
    gridline-color: {BORDER};
    border: 1px solid {BORDER};
    selection-background-color: {GOLD_LIGHT};
    selection-color: {TEXT_DARK};
}}
QHeaderView::section {{
    background-color: {NAVY};
    color: {WHITE};
    padding: 6px;
    border: none;
    border-right: 1px solid {NAVY_DARK};
    font-weight: 600;
}}
QTabWidget::pane {{
    border: 1px solid {BORDER};
    background-color: {WHITE};
    top: -1px;
}}
QTabBar::tab {{
    background-color: {CREAM_DARK};
    color: {TEXT_DARK};
    border: 1px solid {BORDER};
    border-bottom: none;
    padding: 8px 18px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {WHITE};
    color: {NAVY};
    border-bottom: 2px solid {GOLD};
    font-weight: 600;
}}
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: 600;
    color: {NAVY};
    background-color: {WHITE};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}}
QListWidget {{
    background-color: {WHITE};
    border: 1px solid {BORDER};
}}
QMenu {{
    background-color: {WHITE};
    border: 1px solid {BORDER};
}}
QMenu::item:selected {{
    background-color: {GOLD_LIGHT};
    color: {TEXT_DARK};
}}
QStatusBar {{
    background-color: {NAVY_DARK};
    color: {WHITE};
}}
QScrollBar:vertical {{
    background: {CREAM};
    width: 12px;
}}
QScrollBar::handle:vertical {{
    background: {CREAM_DARK};
    border: 1px solid {BORDER};
    min-height: 24px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: {GOLD_LIGHT};
}}
"""
