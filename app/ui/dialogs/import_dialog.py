"""Import backup dialog: pick a ZIP, preview counts, confirm, run import."""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from services import import_service
from ui.theme import DANGER


class ImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("นำเข้าข้อมูล (Import)")
        self.setMinimumWidth(480)
        self._selected_path: Path | None = None
        self._inspect_result = None

        layout = QVBoxLayout(self)

        self.info_label = QLabel(
            "เลือกไฟล์ Backup (.zip) ที่ต้องการนำเข้า\n"
            "ระบบจะสำรองข้อมูลปัจจุบันไว้ก่อนโดยอัตโนมัติ"
        )
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        choose_btn = QPushButton("เลือกไฟล์ Backup...")
        choose_btn.clicked.connect(self._choose_file)
        layout.addWidget(choose_btn)

        self.preview_label = QLabel()
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("margin-top: 8px;")
        layout.addWidget(self.preview_label)

        self.error_label = QLabel()
        self.error_label.setStyleSheet(f"color: {DANGER};")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("ยืนยันนำเข้า")
        self.buttons.accepted.connect(self._on_confirm)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def _choose_file(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self, "เลือกไฟล์ Backup", "", "StockApp Backup (*.zip)"
        )
        if not path_str:
            return

        self._selected_path = Path(path_str)
        self.error_label.hide()
        result = import_service.inspect_backup_zip(self._selected_path)
        self._inspect_result = result

        if not result.ok:
            self.preview_label.setText("")
            self.error_label.setText("\n".join(result.errors))
            self.error_label.show()
            self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
            return

        self.preview_label.setText(
            f"ไฟล์: {self._selected_path.name}\n"
            f"วันที่ Export: {result.export_date}\n"
            f'จะนำเข้า — วัสดุ: {result.counts.get("items", 0)} รายการ, '
            f'เอกสาร: {result.counts.get("transactions", 0)} รายการ, '
            f'ประเภทวัสดุ: {result.counts.get("categories", 0)} รายการ\n\n'
            "คำเตือน: ข้อมูลปัจจุบันทั้งหมดจะถูกแทนที่ด้วยข้อมูลจากไฟล์นี้ "
            "(ระบบจะสำรองข้อมูลปัจจุบันไว้ให้ก่อน)"
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

    def _on_confirm(self) -> None:
        if not self._selected_path or not self._inspect_result or not self._inspect_result.ok:
            return

        confirm = QMessageBox.question(
            self,
            "ยืนยันการนำเข้าข้อมูล",
            "ข้อมูลปัจจุบันทั้งหมดจะถูกแทนที่ ต้องการดำเนินการต่อหรือไม่?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        result = import_service.import_backup_zip(self._selected_path)
        if not result.ok:
            QMessageBox.critical(
                self, "นำเข้าข้อมูลล้มเหลว",
                f"เกิดข้อผิดพลาด: {result.error}\nระบบได้กู้คืนข้อมูลเดิมให้แล้ว",
            )
            return

        QMessageBox.information(
            self, "นำเข้าข้อมูลสำเร็จ",
            "นำเข้าข้อมูลสำเร็จ โปรแกรมจะปิดตัวลง กรุณาเปิดโปรแกรมใหม่เพื่อใช้งานข้อมูลล่าสุด",
        )
        self.accept()
