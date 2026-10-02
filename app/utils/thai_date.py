"""Thai (Buddhist Era) date formatting, ported from index.html's getThaiDate()."""
from datetime import date

THAI_MONTHS = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]


def format_thai_date(date_str: str) -> str:
    """'2026-09-28' -> '28 กันยายน 2569' (Buddhist Era = Gregorian + 543)."""
    if not date_str:
        return ""
    y, m, d = (int(p) for p in date_str.split("-"))
    return f"{d} {THAI_MONTHS[m - 1]} {y + 543}"


def current_fiscal_year_be() -> int:
    """Thai fiscal year (Oct 1 - Sep 30) as a Buddhist-Era year."""
    today = date.today()
    fy_ad = today.year + 1 if today.month >= 10 else today.year
    return fy_ad + 543
