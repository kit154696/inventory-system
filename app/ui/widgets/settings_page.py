"""Settings page: org name + Export/Import/Backup (Phase 2)."""
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from database.models import SettingsRepo
from services import backup_service, export_service
from ui.dialogs.import_dialog import ImportDialog
from ui.theme import TEXT_MUTED
from utils.paths import get_backup_dir


class SettingsPage(QWidget):
    org_name_changed = Signal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        general_box = QGroupBox("ข้อมูลทั่วไป")
        form = QFormLayout(general_box)
        self.org_name_edit = QLineEdit()
        save_btn = QPushButton("บันทึก")
        save_btn.clicked.connect(self._save_org_name)
        org_row = QHBoxLayout()
        org_row.addWidget(self.org_name_edit)
        org_row.addWidget(save_btn)
        form.addRow("ชื่อหน่วยงาน", org_row)
        layout.addWidget(general_box)

        backup_box = QGroupBox("สำรอง / นำเข้า-ส่งออกข้อมูล")
        backup_layout = QVBoxLayout(backup_box)

        btn_row = QHBoxLayout()
        export_btn = QPushButton("Export ข้อมูล")
        export_btn.clicked.connect(self._on_export)
        import_btn = QPushButton("Import ข้อมูล")
        import_btn.clicked.connect(self._on_import)
        backup_now_btn = QPushButton("สำรองข้อมูลทันที")
        backup_now_btn.clicked.connect(self._on_backup_now)
        btn_row.addWidget(export_btn)
        btn_row.addWidget(import_btn)
        btn_row.addWidget(backup_now_btn)
        backup_layout.addLayout(btn_row)

        recent_label = QLabel("รายการสำรองข้อมูลล่าสุด (คลิกขวาเพื่อกู้คืน)")
        recent_label.setStyleSheet(f"color: {TEXT_MUTED}; margin-top: 8px;")
        backup_layout.addWidget(recent_label)

        self.backup_list = QListWidget()
        self.backup_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.backup_list.customContextMenuRequested.connect(self._show_backup_context_menu)
        self.backup_list.setMaximumHeight(140)
        backup_layout.addWidget(self.backup_list)

        layout.addWidget(backup_box)
        layout.addStretch()
        self.refresh()

    def refresh(self) -> None:
        self.org_name_edit.setText(SettingsRepo.get("orgName") or "")
        self._reload_backup_list()

    def _reload_backup_list(self) -> None:
        self.backup_list.clear()
        for path in backup_service.list_backups():
            self.backup_list.addItem(QListWidgetItem(path.name))

    def _save_org_name(self) -> None:
        name = self.org_name_edit.text().strip()
        SettingsRepo.set("orgName", name)
        self.org_name_changed.emit(name)
        QMessageBox.information(self, "บันทึกสำเร็จ", "บันทึกชื่อหน่วยงานเรียบร้อยแล้ว")

    def _on_export(self) -> None:
        menu = QMenu(self)
        zip_action = menu.addAction("ZIP Backup (.zip)")
        json_action = menu.addAction("JSON (.json)")
        csv_action = menu.addAction("CSV (แยกไฟล์ตามตาราง)")
        chosen = menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))

        if chosen == zip_action:
            self._export_zip()
        elif chosen == json_action:
            self._export_json()
        elif chosen == csv_action:
            self._export_csv()

    def _export_zip(self) -> None:
        from datetime import date
        default_name = f"stockapp_backup_{date.today().isoformat()}.zip"
        path_str, _ = QFileDialog.getSaveFileName(self, "Export ZIP Backup", default_name, "ZIP (*.zip)")
        if not path_str:
            return
        try:
            export_service.export_zip(Path(path_str))
            QMessageBox.information(self, "Export สำเร็จ", f"บันทึกไฟล์แล้วที่:\n{path_str}")
        except Exception as e:
            QMessageBox.critical(self, "Export ล้มเหลว", str(e))

    def _export_json(self) -> None:
        path_str, _ = QFileDialog.getSaveFileName(self, "Export JSON", "stockapp_export.json", "JSON (*.json)")
        if not path_str:
            return
        try:
            export_service.export_json(Path(path_str))
            QMessageBox.information(self, "Export สำเร็จ", f"บันทึกไฟล์แล้วที่:\n{path_str}")
        except Exception as e:
            QMessageBox.critical(self, "Export ล้มเหลว", str(e))

    def _export_csv(self) -> None:
        dir_str = QFileDialog.getExistingDirectory(self, "เลือกโฟลเดอร์สำหรับบันทึกไฟล์ CSV")
        if not dir_str:
            return
        try:
            files = export_service.export_csv(Path(dir_str))
            names = "\n".join(f.name for f in files)
            QMessageBox.information(self, "Export สำเร็จ", f"บันทึกไฟล์แล้วที่ {dir_str}:\n{names}")
        except Exception as e:
            QMessageBox.critical(self, "Export ล้มเหลว", str(e))

    def _on_import(self) -> None:
        dialog = ImportDialog(self)
        if dialog.exec():
            QApplication.instance().quit()

    def _on_backup_now(self) -> None:
        try:
            path = backup_service.create_auto_backup()
            self._reload_backup_list()
            QMessageBox.information(self, "สำรองข้อมูลสำเร็จ", f"สร้างไฟล์สำรองแล้ว:\n{path.name}")
        except Exception as e:
            QMessageBox.critical(self, "สำรองข้อมูลล้มเหลว", str(e))

    def _show_backup_context_menu(self, pos) -> None:
        item = self.backup_list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        restore_action = menu.addAction("กู้คืนข้อมูลนี้")
        chosen = menu.exec(self.backup_list.mapToGlobal(pos))
        if chosen == restore_action:
            self._restore_backup(item.text())

    def _restore_backup(self, filename: str) -> None:
        confirm = QMessageBox.question(
            self,
            "ยืนยันการกู้คืนข้อมูล",
            f'ต้องการกู้คืนข้อมูลจาก "{filename}" หรือไม่?\n'
            "ข้อมูลปัจจุบันทั้งหมดจะถูกแทนที่ (โปรแกรมจะปิดตัวลงหลังกู้คืนสำเร็จ)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            backup_path = get_backup_dir() / filename
            backup_service.restore_db_file(backup_path)
            QMessageBox.information(self, "กู้คืนสำเร็จ", "กู้คืนข้อมูลสำเร็จ โปรแกรมจะปิดตัวลง")
            QApplication.instance().quit()
        except Exception as e:
            QMessageBox.critical(self, "กู้คืนล้มเหลว", str(e))
