"""Main application window: sidebar navigation + stacked pages."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from database.models import SettingsRepo
from ui.theme import CREAM, GOLD, GOLD_DARK, NAVY, NAVY_DARK, NAVY_LIGHT, WHITE
from ui.widgets.dashboard_page import DashboardPage
from ui.widgets.items_page import ItemsPage
from ui.widgets.reports_page import ReportsPage
from ui.widgets.settings_page import SettingsPage
from ui.widgets.transactions_page import TransactionsPage

NAV_ITEMS = [
    ("แดชบอร์ด", "dashboard"),
    ("ทะเบียนคุมวัสดุ", "items"),
    ("รับเข้า / เบิกจ่าย", "transactions"),
    ("รายงาน", "reports"),
    ("ตั้งค่า", "settings"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ระบบทะเบียนคุมวัสดุ")
        self.resize(1280, 800)

        central = QWidget()
        self.setCentralWidget(central)
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        outer_layout.addWidget(self._build_header())

        body = QWidget()
        root_layout = QHBoxLayout(body)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        outer_layout.addWidget(body, stretch=1)

        self.sidebar = self._build_sidebar()
        root_layout.addWidget(self.sidebar)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(28, 22, 28, 20)

        self.title_label = QLabel()
        self.title_label.setObjectName("pageTitle")
        right_layout.addWidget(self.title_label)

        self.stack = QStackedWidget()
        right_layout.addWidget(self.stack)
        root_layout.addWidget(right, stretch=1)

        self.pages = {}
        self._build_pages()

        self.setStatusBar(QStatusBar())

        self.sidebar.currentRowChanged.connect(self._on_nav_changed)
        self.sidebar.setCurrentRow(0)

        self._apply_styles()

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("appHeader")
        header.setFixedHeight(64)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)

        crest = QLabel("ตราครุฑ")
        crest.setObjectName("crestBadge")
        crest.setAlignment(Qt.AlignmentFlag.AlignCenter)
        crest.setFixedSize(40, 40)
        layout.addWidget(crest)

        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        app_title = QLabel("ระบบทะเบียนคุมวัสดุ")
        app_title.setObjectName("headerTitle")
        self.org_name_label = QLabel(SettingsRepo.get("orgName") or "")
        self.org_name_label.setObjectName("headerSubtitle")
        text_col.addWidget(app_title)
        text_col.addWidget(self.org_name_label)
        layout.addSpacing(12)
        layout.addLayout(text_col)
        layout.addStretch()
        return header

    def _build_sidebar(self) -> QListWidget:
        sidebar = QListWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        for label, _key in NAV_ITEMS:
            item = QListWidgetItem(label)
            item.setSizeHint(item.sizeHint().expandedTo(item.sizeHint()))
            sidebar.addItem(item)
        return sidebar

    def _build_pages(self) -> None:
        page_classes = {
            "dashboard": DashboardPage,
            "items": ItemsPage,
            "transactions": TransactionsPage,
            "reports": ReportsPage,
            "settings": SettingsPage,
        }
        for _label, key in NAV_ITEMS:
            page = page_classes[key]()
            self.pages[key] = page
            self.stack.addWidget(page)

        self.pages["settings"].org_name_changed.connect(self.org_name_label.setText)

    def _on_nav_changed(self, index: int) -> None:
        label, key = NAV_ITEMS[index]
        self.title_label.setText(label)
        self.stack.setCurrentIndex(index)
        page = self.pages[key]
        if hasattr(page, "refresh"):
            page.refresh()

    def show_status(self, message: str, timeout_ms: int = 3000) -> None:
        self.statusBar().showMessage(message, timeout_ms)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            f"""
            QFrame#appHeader {{
                background-color: {NAVY_DARK};
                border-bottom: 3px solid {GOLD};
            }}
            QLabel#crestBadge {{
                background-color: {GOLD};
                color: {NAVY_DARK};
                border-radius: 20px;
                font-size: 9px;
                font-weight: 700;
            }}
            QLabel#headerTitle {{
                color: {WHITE};
                font-size: 18px;
                font-weight: 700;
            }}
            QLabel#headerSubtitle {{
                color: {GOLD};
                font-size: 12px;
            }}
            QListWidget#sidebar {{
                background-color: {NAVY};
                border: none;
                outline: none;
                padding-top: 12px;
            }}
            QListWidget#sidebar::item {{
                color: {CREAM};
                padding: 14px 22px;
                border: none;
                border-left: 4px solid transparent;
            }}
            QListWidget#sidebar::item:selected {{
                background-color: {NAVY_LIGHT};
                color: {WHITE};
                border-left: 4px solid {GOLD};
                font-weight: 600;
            }}
            QListWidget#sidebar::item:hover:!selected {{
                background-color: {NAVY_DARK};
            }}
            QLabel#pageTitle {{
                font-size: 21px;
                font-weight: 700;
                color: {NAVY};
                border-bottom: 2px solid {GOLD_DARK};
                padding-bottom: 10px;
                margin-bottom: 14px;
            }}
            """
        )
