"""Transaction (IN/OUT document) entry dialog."""
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from database.models import InsufficientStockError, TransactionRepo
from ui.dialogs.item_picker_dialog import ItemPickerDialog
from ui.theme import DANGER
from utils.validators import validate_transaction

COL_CODE, COL_NAME, COL_UNIT, COL_QTY, COL_PRICE, COL_SUBTOTAL = range(6)
COLS = ["รหัส", "ชื่อวัสดุ", "หน่วยนับ", "จำนวน", "ราคา/หน่วย", "รวม"]


class TransactionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("บันทึกเอกสารรับเข้า / เบิกจ่าย")
        self.setMinimumSize(760, 580)
        self._line_items: list[dict] = []  # parallel to table rows

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self._suggest_doc_no)

        self.type_combo = QComboBox()
        self.type_combo.addItem("รับเข้า (IN)", "IN")
        self.type_combo.addItem("เบิกจ่าย (OUT)", "OUT")
        self.type_combo.currentIndexChanged.connect(self._suggest_doc_no)

        doc_row = QHBoxLayout()
        self.doc_no_edit = QLineEdit()
        gen_btn = QPushButton("สร้างเลขที่อัตโนมัติ")
        gen_btn.clicked.connect(self._suggest_doc_no)
        doc_row.addWidget(self.doc_no_edit)
        doc_row.addWidget(gen_btn)

        self.ref_edit = QLineEdit()
        self.note_edit = QLineEdit()
        self.user_name_edit = QLineEdit()
        self.approver_edit = QLineEdit()
        self.checker_edit = QLineEdit()

        form.addRow("วันที่ *", self.date_edit)
        form.addRow("ประเภท *", self.type_combo)
        form.addRow("เลขที่เอกสาร *", doc_row)
        form.addRow("เลขที่อ้างอิง", self.ref_edit)
        form.addRow("หมายเหตุ", self.note_edit)
        form.addRow("ผู้บันทึก", self.user_name_edit)
        form.addRow("ผู้อนุมัติ", self.approver_edit)
        form.addRow("ผู้ตรวจสอบ", self.checker_edit)

        line_header = QHBoxLayout()
        line_header.addWidget(QLabel("รายการวัสดุ"))
        line_header.addStretch()
        add_line_btn = QPushButton("+ เพิ่มรายการ")
        add_line_btn.clicked.connect(self._add_line)
        remove_line_btn = QPushButton("ลบรายการที่เลือก")
        remove_line_btn.clicked.connect(self._remove_selected_line)
        line_header.addWidget(add_line_btn)
        line_header.addWidget(remove_line_btn)
        layout.addLayout(line_header)

        self.table = QTableWidget(0, len(COLS))
        self.table.setHorizontalHeaderLabels(COLS)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        self.total_label = QLabel("รวมทั้งสิ้น: 0.00 บาท")
        self.total_label.setStyleSheet("font-weight: 600; font-size: 14px;")
        layout.addWidget(self.total_label)

        self.error_label = QLabel()
        self.error_label.setStyleSheet(f"color: {DANGER};")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._suggest_doc_no()

    def _suggest_doc_no(self) -> None:
        type_ = self.type_combo.currentData()
        d = self.date_edit.date().toString("yyyy-MM-dd")
        try:
            self.doc_no_edit.setText(TransactionRepo.next_doc_no(type_, d))
        except Exception:
            pass

    def _add_line(self) -> None:
        picker = ItemPickerDialog(self)
        if picker.exec() != QDialog.DialogCode.Accepted or not picker.selected_item:
            return
        item = picker.selected_item
        self._line_items.append(
            {
                "item_id": item.id,
                "code": item.code,
                "name": item.name,
                "spec": item.spec,
                "unit": item.unit,
                "qty": 1.0,
                "price": item.last_price,
            }
        )
        self._render_table()

    def _remove_selected_line(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._line_items):
            return
        del self._line_items[row]
        self._render_table()

    def _on_qty_changed(self, row: int, value: float) -> None:
        if row < len(self._line_items):
            self._line_items[row]["qty"] = value
            self._update_subtotal(row)

    def _on_price_changed(self, row: int, value: float) -> None:
        if row < len(self._line_items):
            self._line_items[row]["price"] = value
            self._update_subtotal(row)

    def _update_subtotal(self, row: int) -> None:
        line = self._line_items[row]
        subtotal_item = self.table.item(row, COL_SUBTOTAL)
        if subtotal_item:
            subtotal_item.setText(f'{line["qty"] * line["price"]:,.2f}')
        self._update_total()

    def _update_total(self) -> None:
        total = sum(line["qty"] * line["price"] for line in self._line_items)
        self.total_label.setText(f"รวมทั้งสิ้น: {total:,.2f} บาท")

    def _render_table(self) -> None:
        self.table.setRowCount(len(self._line_items))
        for row, line in enumerate(self._line_items):
            self.table.setItem(row, COL_CODE, QTableWidgetItem(line["code"]))
            self.table.setItem(row, COL_NAME, QTableWidgetItem(line["name"]))
            self.table.setItem(row, COL_UNIT, QTableWidgetItem(line["unit"]))

            qty_spin = QDoubleSpinBox()
            qty_spin.setRange(0.01, 1_000_000)
            qty_spin.setDecimals(2)
            qty_spin.setValue(line["qty"])
            qty_spin.valueChanged.connect(lambda v, r=row: self._on_qty_changed(r, v))
            self.table.setCellWidget(row, COL_QTY, qty_spin)

            price_spin = QDoubleSpinBox()
            price_spin.setRange(0, 1_000_000_000)
            price_spin.setDecimals(2)
            price_spin.setValue(line["price"])
            price_spin.valueChanged.connect(lambda v, r=row: self._on_price_changed(r, v))
            self.table.setCellWidget(row, COL_PRICE, price_spin)

            subtotal_item = QTableWidgetItem(f'{line["qty"] * line["price"]:,.2f}')
            subtotal_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, COL_SUBTOTAL, subtotal_item)

        self._update_total()

    def _on_save(self) -> None:
        payload = {
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "type": self.type_combo.currentData(),
            "doc_no": self.doc_no_edit.text(),
            "ref": self.ref_edit.text(),
            "note": self.note_edit.text(),
            "user_name": self.user_name_edit.text(),
            "approver": self.approver_edit.text(),
            "checker": self.checker_edit.text(),
            "lines": [
                {
                    "item_id": line["item_id"],
                    "code": line["code"],
                    "name": line["name"],
                    "spec": line["spec"],
                    "unit": line["unit"],
                    "qty": line["qty"],
                    "price": line["price"],
                }
                for line in self._line_items
            ],
        }
        ok, errors, cleaned = validate_transaction(payload)
        if not ok:
            self.error_label.setText("\n".join(errors))
            self.error_label.show()
            return

        try:
            TransactionRepo.create(cleaned, cleaned["lines"])
        except InsufficientStockError as e:
            self.error_label.setText(str(e))
            self.error_label.show()
            return
        except Exception as e:
            QMessageBox.critical(self, "เกิดข้อผิดพลาด", str(e))
            return

        self.accept()
