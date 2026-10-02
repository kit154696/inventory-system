"""Reports page: stock-on-hand report + per-item stockcard ledger + annual report."""
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.models import CategoryRepo, ItemRepo, ReportRepo, SettingsRepo
from services import print_service, report_export_service
from utils.thai_date import current_fiscal_year_be

STOCK_COLS = ["รหัส", "ชื่อวัสดุ", "ประเภท", "หน่วยนับ", "คงเหลือ", "ราคาล่าสุด", "มูลค่ารวม"]
CARD_COLS = ["วันที่", "ประเภท", "เลขที่เอกสาร", "จำนวน", "ราคา", "คงเหลือ"]
ANNUAL_COLS = ["ลำดับ", "ประเภท", "รายการ", "หน่วยนับ", "ยอดยกมา", "รับเข้า", "จ่ายออก", "คงเหลือ"]
TYPE_LABELS = {"IN": "รับเข้า", "OUT": "เบิกจ่าย"}


class StockReportTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.cat_combo = QComboBox()
        self.cat_combo.addItem("ทุกประเภท", None)
        for cat in CategoryRepo.list_all():
            self.cat_combo.addItem(f'{cat["code"]} - {cat["name"]}', cat["code"])
        refresh_btn = QPushButton("แสดงรายงาน")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(self.cat_combo)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.total_label = QLabel()
        layout.addWidget(self.total_label)

        self.table = QTableWidget(0, len(STOCK_COLS))
        self.table.setHorizontalHeaderLabels(STOCK_COLS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self) -> None:
        cat_code = self.cat_combo.currentData()
        rows = ReportRepo.stock_report(cat_code=cat_code)
        self.table.setRowCount(len(rows))
        total_value = 0.0
        for row, r in enumerate(rows):
            self.table.setItem(row, 0, QTableWidgetItem(r["code"]))
            self.table.setItem(row, 1, QTableWidgetItem(r["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(r["cat_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(r["unit"]))
            self.table.setItem(row, 4, QTableWidgetItem(f'{r["balance"]:g}'))
            self.table.setItem(row, 5, QTableWidgetItem(f'{r["last_price"]:,.2f}'))
            self.table.setItem(row, 6, QTableWidgetItem(f'{r["total_value"]:,.2f}'))
            total_value += r["total_value"]
        self.total_label.setText(f"จำนวนรายการ: {len(rows)}  |  มูลค่ารวม: {total_value:,.2f} บาท")


class StockCardTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.item_combo = QComboBox()
        for item in ItemRepo.list():
            self.item_combo.addItem(f"{item.code} - {item.name}", item.id)
        self.item_combo.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.item_combo)
        toolbar.addStretch()
        print_btn = QPushButton("พิมพ์บัตรคุมวัสดุ")
        print_btn.clicked.connect(self._on_print)
        toolbar.addWidget(print_btn)
        layout.addLayout(toolbar)

        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        self.table = QTableWidget(0, len(CARD_COLS))
        self.table.setHorizontalHeaderLabels(CARD_COLS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        if self.item_combo.count():
            self.refresh()

    def refresh(self) -> None:
        item_id = self.item_combo.currentData()
        if item_id is None:
            return
        item, movements = ReportRepo.stockcard(item_id)
        if item is None:
            return
        self.info_label.setText(
            f"{item.code} — {item.name}  |  หน่วยนับ: {item.unit}  |  ขั้นต่ำ: {item.min_qty:g}"
        )
        self.table.setRowCount(len(movements))
        for row, m in enumerate(movements):
            self.table.setItem(row, 0, QTableWidgetItem(m["date"]))
            self.table.setItem(row, 1, QTableWidgetItem(TYPE_LABELS.get(m["type"], m["type"])))
            self.table.setItem(row, 2, QTableWidgetItem(m["doc_no"]))
            self.table.setItem(row, 3, QTableWidgetItem(f'{m["qty"]:g}'))
            self.table.setItem(row, 4, QTableWidgetItem(f'{m["price"]:,.2f}'))
            self.table.setItem(row, 5, QTableWidgetItem(f'{m["balance"]:g}'))

    def _on_print(self) -> None:
        item_id = self.item_combo.currentData()
        if item_id is None:
            return
        item, movements = ReportRepo.stockcard(item_id)
        if item is None:
            return
        html = print_service.stockcard_html(item, movements)
        print_service.show_print_preview(self, html, f"บัตรคุมวัสดุ - {item.code}")


class AnnualReportTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.fy_spin = QSpinBox()
        self.fy_spin.setRange(2500, 2700)
        self.fy_spin.setValue(current_fiscal_year_be())
        self.cat_combo = QComboBox()
        self.cat_combo.addItem("ทุกประเภท", None)
        for cat in CategoryRepo.list_all():
            self.cat_combo.addItem(f'{cat["code"]} - {cat["name"]}', cat["code"])
        show_btn = QPushButton("แสดงรายงาน")
        show_btn.clicked.connect(self.refresh)
        export_btn = QPushButton("Export Excel")
        export_btn.clicked.connect(self._on_export_excel)
        print_btn = QPushButton("พิมพ์")
        print_btn.clicked.connect(self._on_print)

        toolbar.addWidget(QLabel("ปีงบประมาณ (พ.ศ.)"))
        toolbar.addWidget(self.fy_spin)
        toolbar.addWidget(self.cat_combo)
        toolbar.addWidget(show_btn)
        toolbar.addStretch()
        toolbar.addWidget(export_btn)
        toolbar.addWidget(print_btn)
        layout.addLayout(toolbar)

        self.total_label = QLabel()
        layout.addWidget(self.total_label)

        self.table = QTableWidget(0, len(ANNUAL_COLS))
        self.table.setHorizontalHeaderLabels(ANNUAL_COLS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self._rows: list = []
        self._totals: dict = {}
        self.refresh()

    def refresh(self) -> None:
        fy = self.fy_spin.value()
        cat_code = self.cat_combo.currentData()
        self._rows, self._totals = ReportRepo.annual_summary(fy, cat_code)

        self.table.setRowCount(len(self._rows))
        for row, r in enumerate(self._rows):
            self.table.setItem(row, 0, QTableWidgetItem(str(r["no"])))
            self.table.setItem(row, 1, QTableWidgetItem(r["cat_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(r["name"]))
            self.table.setItem(row, 3, QTableWidgetItem(r["unit"]))
            self.table.setItem(row, 4, QTableWidgetItem(f'{r["brought_forward"]:g}'))
            self.table.setItem(row, 5, QTableWidgetItem(f'{r["received"]:g}'))
            self.table.setItem(row, 6, QTableWidgetItem(f'{r["issued"]:g}'))
            self.table.setItem(row, 7, QTableWidgetItem(f'{r["balance"]:g}'))

        t = self._totals
        self.total_label.setText(
            f'จำนวนรายการ: {len(self._rows)}  |  '
            f'ยอดยกมา: {t.get("brought_forward", 0):g}  |  '
            f'รับเข้า: {t.get("received", 0):g}  |  '
            f'จ่ายออก: {t.get("issued", 0):g}  |  '
            f'คงเหลือ: {t.get("balance", 0):g}'
        )

    def _category_label(self) -> str:
        cat_code = self.cat_combo.currentData()
        if not cat_code:
            return "รวมทุกประเภท"
        cat = CategoryRepo.get(cat_code)
        return cat["name"] if cat else "รวมทุกประเภท"

    def _on_export_excel(self) -> None:
        fy = self.fy_spin.value()
        default_name = f"รายงานรับจ่ายพัสดุ_ปีงบ{fy}.xlsx"
        path_str, _ = QFileDialog.getSaveFileName(self, "Export Excel", default_name, "Excel (*.xlsx)")
        if not path_str:
            return
        try:
            report_export_service.export_annual_report_excel(path_str, fy, self.cat_combo.currentData())
            QMessageBox.information(self, "Export สำเร็จ", f"บันทึกไฟล์แล้วที่:\n{path_str}")
        except Exception as e:
            QMessageBox.critical(self, "Export ล้มเหลว", str(e))

    def _on_print(self) -> None:
        org_name = SettingsRepo.get("orgName") or "ระบบทะเบียนคุมวัสดุ"
        html = print_service.annual_report_html(
            self._rows, self._totals, org_name, self._category_label(), self.fy_spin.value()
        )
        print_service.show_print_preview(self, html, "รายงานรับจ่ายพัสดุประจำปีงบประมาณ", landscape=True)


class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        self.stock_tab = StockReportTab()
        self.card_tab = StockCardTab()
        self.annual_tab = AnnualReportTab()
        tabs.addTab(self.stock_tab, "รายงานคงเหลือ")
        tabs.addTab(self.card_tab, "บัตรคุมวัสดุ (Stockcard)")
        tabs.addTab(self.annual_tab, "รายงานประจำปีงบประมาณ")
        layout.addWidget(tabs)

    def refresh(self) -> None:
        self.stock_tab.refresh()
        self.card_tab.refresh()
        self.annual_tab.refresh()
