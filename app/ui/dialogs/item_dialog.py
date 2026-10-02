"""Add/Edit item dialog."""
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

from database.models import CategoryRepo, DuplicateCodeError, Item, ItemRepo
from ui.theme import DANGER
from utils.validators import validate_item


class ItemDialog(QDialog):
    def __init__(self, parent=None, item: Item | None = None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle("แก้ไขวัสดุ" if item else "เพิ่มวัสดุใหม่")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self.code_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.spec_edit = QLineEdit()
        self.cat_combo = QComboBox()
        for cat in CategoryRepo.list_all():
            self.cat_combo.addItem(f'{cat["code"]} - {cat["name"]}', cat["code"])
        self.unit_edit = QLineEdit()
        self.min_qty_spin = QSpinBox()
        self.min_qty_spin.setRange(0, 1_000_000)
        self.min_qty_spin.setValue(5)
        self.location_edit = QLineEdit()
        self.location_edit.setText("กองพัสดุ")
        self.last_price_spin = QDoubleSpinBox()
        self.last_price_spin.setRange(0, 1_000_000_000)
        self.last_price_spin.setDecimals(2)

        form.addRow("รหัสวัสดุ *", self.code_edit)
        form.addRow("ชื่อวัสดุ *", self.name_edit)
        form.addRow("รายละเอียด", self.spec_edit)
        form.addRow("ประเภท *", self.cat_combo)
        form.addRow("หน่วยนับ *", self.unit_edit)
        form.addRow("จำนวนขั้นต่ำ", self.min_qty_spin)
        form.addRow("สถานที่จัดเก็บ", self.location_edit)
        form.addRow("ราคาล่าสุด", self.last_price_spin)

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

        if item:
            self._load_item(item)

    def _load_item(self, item: Item) -> None:
        self.code_edit.setText(item.code)
        self.name_edit.setText(item.name)
        self.spec_edit.setText(item.spec)
        idx = self.cat_combo.findData(item.cat_code)
        if idx >= 0:
            self.cat_combo.setCurrentIndex(idx)
        self.unit_edit.setText(item.unit)
        self.min_qty_spin.setValue(int(item.min_qty))
        self.location_edit.setText(item.location)
        self.last_price_spin.setValue(item.last_price)

    def _on_save(self) -> None:
        cat_code = self.cat_combo.currentData()
        payload = {
            "code": self.code_edit.text(),
            "name": self.name_edit.text(),
            "spec": self.spec_edit.text() or "-",
            "cat_code": cat_code,
            "cat_name": self.cat_combo.currentText().split(" - ", 1)[-1] if cat_code else "",
            "unit": self.unit_edit.text(),
            "min_qty": self.min_qty_spin.value(),
            "location": self.location_edit.text() or "กองพัสดุ",
            "last_price": self.last_price_spin.value(),
        }
        ok, errors, cleaned = validate_item(payload)
        if not ok:
            self.error_label.setText("\n".join(errors))
            self.error_label.show()
            return

        try:
            if self.item:
                ItemRepo.update(self.item.id, cleaned)
            else:
                ItemRepo.create(cleaned)
        except DuplicateCodeError as e:
            self.error_label.setText(str(e))
            self.error_label.show()
            return
        except Exception as e:
            QMessageBox.critical(self, "เกิดข้อผิดพลาด", str(e))
            return

        self.accept()
