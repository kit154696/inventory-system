"""Reusable prev/next pagination control for list pages."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

PAGE_SIZE = 50


class PaginationBar(QWidget):
    page_changed = Signal(int)

    def __init__(self):
        super().__init__()
        self._page = 0
        self._total = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)

        self.range_label = QLabel()
        self.prev_btn = QPushButton("< ก่อนหน้า")
        self.prev_btn.clicked.connect(self._go_prev)
        self.page_label = QLabel()
        self.next_btn = QPushButton("ถัดไป >")
        self.next_btn.clicked.connect(self._go_next)

        layout.addWidget(self.range_label)
        layout.addStretch()
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.page_label)
        layout.addWidget(self.next_btn)

        self._update_labels()

    @property
    def offset(self) -> int:
        return self._page * PAGE_SIZE

    @property
    def page_count(self) -> int:
        if self._total == 0:
            return 1
        return (self._total + PAGE_SIZE - 1) // PAGE_SIZE

    def set_total(self, total: int) -> None:
        self._total = max(0, total)
        max_page = self.page_count - 1
        if self._page > max_page:
            self._page = max_page
        self._update_labels()

    def reset(self) -> None:
        self._page = 0
        self._update_labels()

    def _go_prev(self) -> None:
        if self._page > 0:
            self._page -= 1
            self._update_labels()
            self.page_changed.emit(self._page)

    def _go_next(self) -> None:
        if self._page < self.page_count - 1:
            self._page += 1
            self._update_labels()
            self.page_changed.emit(self._page)

    def _update_labels(self) -> None:
        self.page_label.setText(f"หน้า {self._page + 1} จาก {self.page_count}")
        if self._total == 0:
            self.range_label.setText("ไม่พบข้อมูล")
        else:
            start = self.offset + 1
            end = min(self.offset + PAGE_SIZE, self._total)
            self.range_label.setText(f"แสดง {start}-{end} จาก {self._total} รายการ")
        self.prev_btn.setEnabled(self._page > 0)
        self.next_btn.setEnabled(self._page < self.page_count - 1)
