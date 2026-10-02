"""Searchable item picker used by the transaction line-item entry flow."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from database.models import Item, ItemRepo


class ItemPickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("เลือกวัสดุ")
        self.setMinimumSize(560, 480)
        self.selected_item: Item | None = None

        layout = QVBoxLayout(self)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("ค้นหารหัสหรือชื่อวัสดุ...")
        self.search_edit.textChanged.connect(self._on_search)
        layout.addWidget(self.search_edit)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["รหัส", "ชื่อวัสดุ", "หน่วยนับ", "คงเหลือ"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.doubleClicked.connect(self._on_accept)
        layout.addWidget(self.table)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._items: list[Item] = []
        self._reload("")

    def _on_search(self, text: str) -> None:
        self._reload(text)

    def _reload(self, search: str) -> None:
        self._items = ItemRepo.list(search=search or None)
        bal_map = ItemRepo.balance_all()
        self.table.setRowCount(len(self._items))
        for row, item in enumerate(self._items):
            self.table.setItem(row, 0, QTableWidgetItem(item.code))
            self.table.setItem(row, 1, QTableWidgetItem(item.name))
            self.table.setItem(row, 2, QTableWidgetItem(item.unit))
            bal = bal_map.get(item.id, 0.0)
            self.table.setItem(row, 3, QTableWidgetItem(f"{bal:g}"))

    def _on_accept(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._items):
            return
        self.selected_item = self._items[row]
        self.accept()
