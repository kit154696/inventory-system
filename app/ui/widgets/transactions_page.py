"""Transactions page: document list + create/delete/view/print."""
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.models import SettingsRepo, TransactionRepo
from services import print_service
from ui.dialogs.transaction_dialog import TransactionDialog
from ui.widgets.pagination_bar import PAGE_SIZE, PaginationBar

COLS = ["เลขที่เอกสาร", "วันที่", "ประเภท", "รายการ", "ผู้บันทึก", "พิมพ์"]
TYPE_LABELS = {"IN": "รับเข้า", "OUT": "เบิกจ่าย"}


class TransactionsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.type_filter = QComboBox()
        self.type_filter.addItem("ทั้งหมด", None)
        self.type_filter.addItem("รับเข้า (IN)", "IN")
        self.type_filter.addItem("เบิกจ่าย (OUT)", "OUT")
        self.type_filter.currentIndexChanged.connect(lambda: self.refresh())

        add_btn = QPushButton("+ บันทึกเอกสารใหม่")
        add_btn.clicked.connect(self._on_add)
        delete_btn = QPushButton("ลบเอกสาร")
        delete_btn.clicked.connect(self._on_delete)

        toolbar.addWidget(self.type_filter)
        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        toolbar.addWidget(delete_btn)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, len(COLS))
        self.table.setHorizontalHeaderLabels(COLS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.pagination = PaginationBar()
        self.pagination.page_changed.connect(self._on_page_changed)
        layout.addWidget(self.pagination)

        self._txs: list = []
        self.refresh()

    def refresh(self, reset_page: bool = True) -> None:
        if reset_page:
            self.pagination.reset()
        type_ = self.type_filter.currentData()

        total = TransactionRepo.count(type_=type_)
        self.pagination.set_total(total)
        self._txs = TransactionRepo.list(type_=type_, limit=PAGE_SIZE, offset=self.pagination.offset)

        self.table.setRowCount(len(self._txs))
        for row, tx in enumerate(self._txs):
            self.table.setItem(row, 0, QTableWidgetItem(tx.doc_no))
            self.table.setItem(row, 1, QTableWidgetItem(tx.date))
            self.table.setItem(row, 2, QTableWidgetItem(TYPE_LABELS.get(tx.type, tx.type)))
            self.table.setItem(row, 3, QTableWidgetItem(str(len(tx.lines))))
            self.table.setItem(row, 4, QTableWidgetItem(tx.user_name))

            print_btn = QPushButton("พิมพ์")
            print_btn.clicked.connect(lambda _checked=False, tx_id=tx.id: self._on_print(tx_id))
            self.table.setCellWidget(row, 5, print_btn)

    def _on_page_changed(self, _page: int) -> None:
        self.refresh(reset_page=False)

    def _selected_tx(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._txs):
            return None
        return self._txs[row]

    def _on_add(self) -> None:
        dialog = TransactionDialog(self)
        if dialog.exec():
            self.refresh()

    def _on_delete(self) -> None:
        tx = self._selected_tx()
        if not tx:
            QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือกเอกสารที่ต้องการลบ")
            return
        confirm = QMessageBox.question(
            self,
            "ยืนยันการลบ",
            f'ต้องการลบเอกสาร "{tx.doc_no}" หรือไม่? (จะกระทบยอดคงเหลือของวัสดุที่เกี่ยวข้อง)',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        TransactionRepo.delete(tx.id)
        self.refresh(reset_page=False)

    def _on_print(self, tx_id: int) -> None:
        tx = TransactionRepo.get(tx_id)
        if not tx:
            return
        org_name = SettingsRepo.get("orgName") or "ระบบทะเบียนคุมวัสดุ"
        if tx.type == "IN":
            html = print_service.receiving_slip_html(tx, org_name)
            title = f"ใบรับพัสดุ - {tx.doc_no}"
        else:
            html = print_service.withdraw_slip_html(tx, org_name)
            title = f"ใบเบิกพัสดุ - {tx.doc_no}"
        print_service.show_print_preview(self, html, title)
