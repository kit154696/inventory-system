"""Items master page: search/filter + CRUD table."""
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.models import CategoryRepo, ItemInUseError, ItemRepo
from ui.dialogs.item_dialog import ItemDialog
from ui.widgets.pagination_bar import PAGE_SIZE, PaginationBar

COLS = ["รหัส", "ชื่อวัสดุ", "ประเภท", "หน่วยนับ", "คงเหลือ", "ราคาล่าสุด", "จำนวนขั้นต่ำ"]


class ItemsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("ค้นหารหัสหรือชื่อวัสดุ...")
        self.search_edit.textChanged.connect(lambda: self.refresh())

        self.cat_combo = QComboBox()
        self.cat_combo.addItem("ทุกประเภท", None)
        for cat in CategoryRepo.list_all():
            self.cat_combo.addItem(f'{cat["code"]} - {cat["name"]}', cat["code"])
        self.cat_combo.currentIndexChanged.connect(lambda: self.refresh())

        add_btn = QPushButton("+ เพิ่มวัสดุ")
        add_btn.clicked.connect(self._on_add)
        edit_btn = QPushButton("แก้ไข")
        edit_btn.clicked.connect(self._on_edit)
        delete_btn = QPushButton("ลบ")
        delete_btn.clicked.connect(self._on_delete)

        toolbar.addWidget(self.search_edit)
        toolbar.addWidget(self.cat_combo)
        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(delete_btn)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, len(COLS))
        self.table.setHorizontalHeaderLabels(COLS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self._on_edit)
        layout.addWidget(self.table)

        self.pagination = PaginationBar()
        self.pagination.page_changed.connect(self._on_page_changed)
        layout.addWidget(self.pagination)

        self._items: list = []
        self.refresh()

    def refresh(self, reset_page: bool = True) -> None:
        if reset_page:
            self.pagination.reset()
        search = self.search_edit.text().strip() or None
        cat_code = self.cat_combo.currentData()

        total = ItemRepo.count(search=search, cat_code=cat_code)
        self.pagination.set_total(total)
        self._items = ItemRepo.list(
            search=search, cat_code=cat_code,
            page_size=PAGE_SIZE, offset=self.pagination.offset,
        )
        bal_map = ItemRepo.balance_all()

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self._items))
        for row, item in enumerate(self._items):
            bal = bal_map.get(item.id, 0.0)
            self.table.setItem(row, 0, QTableWidgetItem(item.code))
            self.table.setItem(row, 1, QTableWidgetItem(item.name))
            self.table.setItem(row, 2, QTableWidgetItem(item.cat_name))
            self.table.setItem(row, 3, QTableWidgetItem(item.unit))
            self.table.setItem(row, 4, QTableWidgetItem(f"{bal:g}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{item.last_price:,.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{item.min_qty:g}"))
        self.table.setSortingEnabled(True)

    def _on_page_changed(self, _page: int) -> None:
        self.refresh(reset_page=False)

    def _selected_item(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._items):
            return None
        return self._items[row]

    def _on_add(self) -> None:
        dialog = ItemDialog(self)
        if dialog.exec():
            self.refresh()

    def _on_edit(self) -> None:
        item = self._selected_item()
        if not item:
            QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือกรายการที่ต้องการแก้ไข")
            return
        dialog = ItemDialog(self, item=item)
        if dialog.exec():
            self.refresh(reset_page=False)

    def _on_delete(self) -> None:
        item = self._selected_item()
        if not item:
            QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือกรายการที่ต้องการลบ")
            return
        confirm = QMessageBox.question(
            self,
            "ยืนยันการลบ",
            f'ต้องการลบวัสดุ "{item.name}" ({item.code}) หรือไม่?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            ItemRepo.delete(item.id)
            self.refresh(reset_page=False)
        except ItemInUseError as e:
            QMessageBox.critical(self, "ไม่สามารถลบได้", str(e))
