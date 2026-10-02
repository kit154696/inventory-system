"""Dashboard page: stat cards + low-stock alert list."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.models import ReportRepo
from ui.theme import BORDER, DANGER, GOLD_DARK, NAVY, SUCCESS, TEXT_DARK, TEXT_MUTED, WHITE


class StatCard(QFrame):
    def __init__(self, title: str, value: str, color: str = NAVY):
        super().__init__()
        self.setObjectName("statCard")
        self.setStyleSheet(
            f"""
            QFrame#statCard {{
                background-color: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 8px;
                border-top: 3px solid {color};
            }}
            """
        )
        layout = QVBoxLayout(self)
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT_DARK};")
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        grid = QGridLayout()
        layout.addLayout(grid)

        self.card_total_items = StatCard("จำนวนวัสดุทั้งหมด", "-", NAVY)
        self.card_total_value = StatCard("มูลค่าคงเหลือรวม", "-", SUCCESS)
        self.card_low_stock = StatCard("รายการใกล้หมด", "-", DANGER)
        self.card_docs_fy = StatCard("เอกสารปีงบประมาณนี้", "-", GOLD_DARK)

        grid.addWidget(self.card_total_items, 0, 0)
        grid.addWidget(self.card_total_value, 0, 1)
        grid.addWidget(self.card_low_stock, 0, 2)
        grid.addWidget(self.card_docs_fy, 0, 3)

        low_stock_label = QLabel("รายการวัสดุใกล้หมด / หมด")
        low_stock_label.setStyleSheet(f"font-weight: 600; color: {NAVY}; margin-top: 16px;")
        layout.addWidget(low_stock_label)

        self.low_stock_list = QListWidget()
        layout.addWidget(self.low_stock_list)

    def refresh(self) -> None:
        data = ReportRepo.dashboard()
        self.card_total_items.set_value(str(data["total_items"]))
        self.card_total_value.set_value(f'{data["total_value"]:,.2f} บาท')
        self.card_low_stock.set_value(str(len(data["low_stock"])))
        self.card_docs_fy.set_value(str(data["docs_this_year"]))

        self.low_stock_list.clear()
        for entry in data["low_stock"]:
            text = f'{entry["name"]}  —  คงเหลือ {entry["balance"]:g} (ขั้นต่ำ {entry["min"]:g})'
            self.low_stock_list.addItem(QListWidgetItem(text))
