"""Print/PDF document builders, ported from index.html's HTML-string print
templates. Each function returns a self-contained HTML string using ONLY
inline styles (no shared <style>/class selectors, and no rowspan/colspan
mixed headers) since QTextDocument's CSS2 subset renders those unreliably.
"""
from PySide6.QtCore import QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrintPreviewDialog, QPrinter

from database.models import Item, Transaction
from utils.thai_date import format_thai_date

_TABLE_STYLE = 'style="width:100%; border-collapse:collapse; font-size:12pt; margin-top:8px;"'
_TH_STYLE = 'style="border:1px solid #000; padding:6px 8px; background:#f0f0f0; text-align:center;"'
_TD_STYLE = 'style="border:1px solid #000; padding:6px 8px;"'
_TD_CENTER = 'style="border:1px solid #000; padding:6px 8px; text-align:center;"'
_TD_RIGHT = 'style="border:1px solid #000; padding:6px 8px; text-align:right;"'


def _th(text: str) -> str:
    return f"<th {_TH_STYLE}>{text}</th>"


def _td(text: str, align: str = "left") -> str:
    style = {"left": _TD_STYLE, "center": _TD_CENTER, "right": _TD_RIGHT}[align]
    return f"<td {style}>{text}</td>"


def stockcard_html(item: Item, movements: list[dict]) -> str:
    header_cells = "".join(
        _th(c) for c in ["วัน เดือน ปี", "รับจาก/จ่ายให้", "เลขที่", "ราคา", "รับ", "จ่าย", "คงเหลือ", "หมายเหตุ"]
    )
    rows_html = (
        f"<tr>{_td('')}{_td('ยอดยกมา')}{_td('')}{_td('')}{_td('')}{_td('')}{_td('')}{_td('')}</tr>"
    )
    for m in movements:
        rows_html += (
            "<tr>"
            + _td(format_thai_date(m["date"]), "center")
            + _td(m.get("ref") or "")
            + _td(m["doc_no"], "center")
            + _td(f'{m["price"]:.2f}' if m["type"] == "IN" else "", "right")
            + _td(f'{m["qty"]:g}' if m["type"] == "IN" else "", "center")
            + _td(f'{m["qty"]:g}' if m["type"] == "OUT" else "", "center")
            + _td(f'<b>{m["balance"]:g}</b>', "center")
            + _td(m.get("note") or "")
            + "</tr>"
        )

    return f"""
    <div style="font-family:'TH SarabunPSK'; font-size:14pt;">
        <div style="display:flex; justify-content:space-between; font-weight:bold;">
            <div>บัญชีวัสดุ</div><div>รหัส {item.code}</div>
        </div>
        <div style="border:1px solid #000; padding:8px; margin:6px 0;">
            <div style="display:flex; justify-content:space-between;">
                <div style="width:33%;">ประเภท: {item.cat_name}</div>
                <div style="width:33%;">ชื่อ: {item.name}</div>
                <div style="width:33%;">หน่วยนับ: {item.unit}</div>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <div style="width:33%;">ขนาด/ลักษณะ: {item.spec}</div>
                <div style="width:33%;">ที่เก็บ: {item.location}</div>
                <div style="width:33%;">Min: {item.min_qty:g}</div>
            </div>
        </div>
        <table {_TABLE_STYLE}>
            <thead><tr>{header_cells}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    """


def _signature_block(entries: list[tuple[str, str]], bordered: bool = False,
                      trailing: tuple[str, str] | None = None) -> str:
    """entries: list of (label, name) pairs, rendered 2-per-row.
    bordered=True draws a boxed signature cell (used by the withdraw slip,
    matching the original's .sign-table). trailing, if given, adds one more
    signer on its own full-width right-aligned row (used by the receiving
    slip's checker signature).
    """
    border = "1px solid #000" if bordered else "none"
    height = "height:120px;" if bordered else ""
    cell_style = f'border:{border}; padding:14px 10px; text-align:center; vertical-align:top; {height}'
    html_rows = []
    for i in range(0, len(entries), 2):
        pair = entries[i:i + 2]
        row_cells = "".join(
            f'<td style="{cell_style}">'
            f'ลงชื่อ.........................................{label}<br>({name or "&nbsp;" * 40})</td>'
            for label, name in pair
        )
        html_rows.append(f"<tr>{row_cells}</tr>")
    if trailing:
        label, name = trailing
        html_rows.append(
            f'<tr><td colspan="2" style="border:{border}; padding:14px 10px; text-align:right;">'
            f'ลงชื่อ.........................................{label}<br>({name or "&nbsp;" * 40})</td></tr>'
        )
    return f'<table style="width:100%; border-collapse:collapse; margin-top:24px;">{"".join(html_rows)}</table>'


def receiving_slip_html(tx: Transaction, org_name: str) -> str:
    rows_html = ""
    total = 0.0
    for i, line in enumerate(tx.lines, start=1):
        subtotal = line.qty * line.price
        total += subtotal
        rows_html += (
            "<tr>"
            + _td(str(i), "center")
            + _td(line.name)
            + _td(f"{line.qty:g}", "center")
            + _td(f"{line.price:,.2f}", "right")
            + _td(f"{subtotal:,.2f}", "right")
            + _td(line.unit, "center")
            + _td("")
            + "</tr>"
        )

    headers = "".join(_th(h) for h in ["ลำดับ", "รายการ", "จำนวน", "ราคา/หน่วย", "รวมเงิน", "หน่วย", "หมายเหตุ"])
    signatures = _signature_block(
        [("ผู้รับพัสดุ", tx.user_name), ("หัวหน้าเจ้าหน้าที่", tx.approver)],
        trailing=("ผู้ตรวจสอบ", tx.checker),
    )

    return f"""
    <div style="font-family:'TH SarabunPSK'; font-size:14pt;">
        <div style="text-align:center; font-weight:bold; font-size:18pt;">{org_name}<br>ใบรับพัสดุ</div>
        <div style="display:flex; justify-content:space-between; margin:10px 0;">
            <div>รายการรับพัสดุตามรายการดังต่อไปนี้</div>
            <div style="text-align:right;">เลขที่ {tx.doc_no}<br>รับจาก {tx.ref}<br>วันที่ {format_thai_date(tx.date)}</div>
        </div>
        <table {_TABLE_STYLE}>
            <thead><tr>{headers}</tr></thead>
            <tbody>{rows_html}</tbody>
            <tfoot><tr>
                <td colspan="4" style="border:1px solid #000; padding:6px 8px; text-align:right;"><b>รวมทั้งสิ้น</b></td>
                <td style="border:1px solid #000; padding:6px 8px; text-align:right;"><b>{total:,.2f}</b></td>
                <td colspan="2" style="border:1px solid #000; padding:6px 8px;"></td>
            </tr></tfoot>
        </table>
        {signatures}
    </div>
    """


def withdraw_slip_html(tx: Transaction, org_name: str) -> str:
    rows_html = ""
    for i, line in enumerate(tx.lines, start=1):
        rows_html += (
            "<tr>"
            + _td(str(i), "center")
            + _td(line.name)
            + _td(f"{line.qty:g}", "center")
            + _td(line.unit, "center")
            + _td("")
            + "</tr>"
        )

    headers = "".join(_th(h) for h in ["ลำดับ", "รายการ", "จำนวนขอเบิก", "หน่วยนับ", "หมายเหตุ"])
    signatures = _signature_block([
        ("ผู้เบิก", tx.user_name), ("ผู้จ่ายพัสดุ", ""),
        ("ผู้สั่งจ่าย", tx.approver), ("ผู้ตรวจสอบ", tx.checker),
    ], bordered=True)

    return f"""
    <div style="font-family:'TH SarabunPSK'; font-size:14pt;">
        <div style="text-align:center; font-weight:bold; font-size:18pt;">{org_name}<br>ใบเบิกพัสดุ</div>
        <div style="text-align:right; margin:10px 0;">
            เลขที่ {tx.doc_no}<br>กอง/ฝ่าย {tx.ref}<br>วันที่ {format_thai_date(tx.date)}
        </div>
        <p>ข้าพเจ้าขอเบิกพัสดุตามรายการต่อไปนี้เพื่อใช้ในงาน..........................................................</p>
        <table {_TABLE_STYLE}>
            <thead><tr>{headers}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        {signatures}
    </div>
    """


def annual_report_html(rows: list[dict], totals: dict, org_name: str,
                        category_label: str, fiscal_year_be: int) -> str:
    headers = "".join(
        _th(h) for h in ["ลำดับ", "ประเภท", "รายการ", "หน่วยนับ", "ยอดยกมา", "รับเข้า", "จ่ายออก", "คงเหลือ", "หมายเหตุ"]
    )
    rows_html = ""
    for r in rows:
        rows_html += (
            "<tr>"
            + _td(str(r["no"]), "center")
            + _td(r["cat_name"])
            + _td(r["name"])
            + _td(r["unit"], "center")
            + _td(f'{r["brought_forward"]:g}', "center")
            + _td(f'{r["received"]:g}', "center")
            + _td(f'{r["issued"]:g}', "center")
            + _td(f'<b>{r["balance"]:g}</b>', "center")
            + _td("")
            + "</tr>"
        )

    return f"""
    <div style="font-family:'TH SarabunPSK'; font-size:13pt;">
        <div style="text-align:center; font-weight:bold; font-size:20pt;">แบบรายงานรับจ่ายพัสดุประจำปีงบประมาณ</div>
        <div style="text-align:center; font-weight:bold; font-size:17pt; margin-bottom:6px;">{org_name}</div>
        <div style="display:flex; justify-content:space-between; font-weight:bold; margin-bottom:6px;">
            <div>รายงานการสำรวจ ปีงบประมาณ {fiscal_year_be}</div>
            <div>{category_label}</div>
        </div>
        <table {_TABLE_STYLE}>
            <thead><tr>{headers}</tr></thead>
            <tbody>{rows_html}</tbody>
            <tfoot><tr>
                <td colspan="4" style="border:1px solid #000; padding:6px 8px; text-align:center;"><b>รวมทั้งสิ้น</b></td>
                <td style="border:1px solid #000; padding:6px 8px; text-align:center;"><b>{totals["brought_forward"]:g}</b></td>
                <td style="border:1px solid #000; padding:6px 8px; text-align:center;"><b>{totals["received"]:g}</b></td>
                <td style="border:1px solid #000; padding:6px 8px; text-align:center;"><b>{totals["issued"]:g}</b></td>
                <td style="border:1px solid #000; padding:6px 8px; text-align:center;"><b>{totals["balance"]:g}</b></td>
                <td style="border:1px solid #000; padding:6px 8px;"></td>
            </tr></tfoot>
        </table>
    </div>
    """


def show_print_preview(parent, html: str, title: str, landscape: bool = False) -> None:
    """Open a QPrintPreviewDialog rendering html on an A4 page (matching the
    original web app's @page rules: portrait/10mm margins for documents,
    landscape/15mm for the wide 9-column annual report). Lets the user print
    to a physical printer or to PDF via the OS print dialog's own PDF driver
    (e.g. Windows' built-in "Microsoft Print to PDF") — no extra PDF library
    needed.

    Known limitation: QTextDocument's renderer does not honor
    page-break-inside:avoid, so a signature block could visually split
    across a page boundary on longer documents.
    """
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setPageOrientation(
        QPageLayout.Orientation.Landscape if landscape else QPageLayout.Orientation.Portrait
    )
    margin_mm = 15.0 if landscape else 10.0
    printer.setPageMargins(QMarginsF(margin_mm, margin_mm, margin_mm, margin_mm), QPageLayout.Unit.Millimeter)

    document = QTextDocument()
    document.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())
    document.setHtml(html)

    dialog = QPrintPreviewDialog(printer, parent)
    dialog.setWindowTitle(title)
    dialog.paintRequested.connect(document.print_)
    dialog.exec()
