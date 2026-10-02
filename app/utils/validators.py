"""Input validation, ported from validators.js (Item/Transaction subset).

Each validate_* function returns (ok: bool, errors: list[str], cleaned: dict|None).
Users/roles/settings-key-whitelist validators are not ported — Phase 1 desktop
app has no login/multi-user concept.
"""
import re
from datetime import date as _date

VALID_CAT_CODES = {
    "A0000", "B0000", "C0000", "D0000", "E0000", "F0000", "G0000",
    "H0000", "I0000", "J0000", "K0000", "L0000", "M0000", "N0000",
    "O0000", "P0000", "Q0000",
}

_TAG_RE = re.compile(r"<[^>]*>")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def sanitize(value):
    """Strip HTML tags and surrounding whitespace from a string value."""
    if not isinstance(value, str):
        return value
    return _TAG_RE.sub("", value).strip()


def sanitize_all(d: dict) -> dict:
    return {k: (sanitize(v) if isinstance(v, str) else v) for k, v in d.items()}


def is_positive_int(val) -> bool:
    try:
        n = float(val)
    except (TypeError, ValueError):
        return False
    return n.is_integer() and n > 0


def is_valid_date(s: str) -> bool:
    if not isinstance(s, str) or not _DATE_RE.match(s):
        return False
    try:
        y, m, d = (int(p) for p in s.split("-"))
        _date(y, m, d)
        return True
    except ValueError:
        return False


def validate_id(id_) -> tuple[bool, list[str]]:
    if not is_positive_int(id_):
        return False, ["ID ต้องเป็นตัวเลขจำนวนเต็มที่มากกว่า 0"]
    return True, []


def validate_item(body: dict) -> tuple[bool, list[str], dict | None]:
    errors: list[str] = []
    b = sanitize_all({
        "code": body.get("code") or "",
        "name": body.get("name") or "",
        "spec": body.get("spec") or "-",
        "cat_code": body.get("cat_code") or "",
        "cat_name": body.get("cat_name") or "",
        "unit": body.get("unit") or "",
        "location": body.get("location") or "กองพัสดุ",
    })

    if not b["code"]:
        errors.append("รหัสวัสดุ (code) ต้องไม่ว่าง")
    elif len(b["code"]) > 20:
        errors.append("รหัสวัสดุ (code) ต้องไม่เกิน 20 ตัวอักษร")

    if not b["name"]:
        errors.append("ชื่อวัสดุ (name) ต้องไม่ว่าง")
    elif len(b["name"]) > 200:
        errors.append("ชื่อวัสดุ (name) ต้องไม่เกิน 200 ตัวอักษร")

    if not b["cat_code"]:
        errors.append("ประเภทวัสดุ (cat_code) ต้องไม่ว่าง")
    elif b["cat_code"] not in VALID_CAT_CODES:
        errors.append(
            f'ประเภทวัสดุ (cat_code) "{b["cat_code"]}" ไม่ถูกต้อง ต้องเป็นหนึ่งใน: '
            + ", ".join(sorted(VALID_CAT_CODES))
        )

    if not b["unit"]:
        errors.append("หน่วยนับ (unit) ต้องไม่ว่าง")

    raw_min_qty = body.get("min_qty")
    min_qty = 0.0
    if raw_min_qty not in (None, ""):
        try:
            min_qty = float(raw_min_qty)
        except (TypeError, ValueError):
            min_qty = float("nan")
    if min_qty != min_qty or min_qty < 0:  # NaN check
        errors.append("จำนวนขั้นต่ำ (min_qty) ต้องเป็นตัวเลข >= 0")

    raw_last_price = body.get("last_price")
    last_price = 0.0
    if raw_last_price not in (None, ""):
        try:
            last_price = float(raw_last_price)
        except (TypeError, ValueError):
            last_price = float("nan")
    if last_price != last_price or last_price < 0:
        errors.append("ราคาล่าสุด (last_price) ต้องเป็นตัวเลข >= 0")

    if errors:
        return False, errors, None

    cleaned = dict(b)
    cleaned["min_qty"] = min_qty
    cleaned["last_price"] = last_price
    return True, [], cleaned


def validate_transaction(body: dict) -> tuple[bool, list[str], dict | None]:
    errors: list[str] = []

    date = sanitize(str(body.get("date") or ""))
    if not date:
        errors.append("วันที่เอกสาร (date) ต้องไม่ว่าง")
    elif not is_valid_date(date):
        errors.append("วันที่เอกสาร (date) ต้องอยู่ในรูปแบบ YYYY-MM-DD และเป็นวันที่ที่ถูกต้อง")

    type_ = sanitize(str(body.get("type") or ""))
    if type_ not in ("IN", "OUT"):
        errors.append('ประเภทเอกสาร (type) ต้องเป็น "IN" (รับเข้า) หรือ "OUT" (เบิกจ่าย) เท่านั้น')

    doc_no = sanitize(str(body.get("doc_no") or ""))
    if not doc_no:
        errors.append("เลขที่เอกสาร (doc_no) ต้องไม่ว่าง")
    elif len(doc_no) > 50:
        errors.append("เลขที่เอกสาร (doc_no) ต้องไม่เกิน 50 ตัวอักษร")

    lines = body.get("lines")
    if not isinstance(lines, list) or len(lines) == 0:
        errors.append("รายการวัสดุ (lines) ต้องมีอย่างน้อย 1 รายการ")
    else:
        for i, line in enumerate(lines):
            num = i + 1
            item_id = line.get("itemId", line.get("item_id"))
            if not is_positive_int(item_id):
                errors.append(f"รายการที่ {num}: item_id ต้องเป็นตัวเลขจำนวนเต็มที่ > 0")

            try:
                qty = float(line.get("qty"))
            except (TypeError, ValueError):
                qty = float("nan")
            if qty != qty or qty <= 0:
                errors.append(f"รายการที่ {num}: จำนวน (qty) ต้องมากกว่า 0")

            try:
                price = float(line.get("price") or 0)
            except (TypeError, ValueError):
                price = float("nan")
            if price != price or price < 0:
                errors.append(f"รายการที่ {num}: ราคา (price) ต้องเป็นตัวเลข >= 0")

            if not line.get("code"):
                errors.append(f"รายการที่ {num}: รหัสวัสดุ (code) ต้องไม่ว่าง")
            if not line.get("name"):
                errors.append(f"รายการที่ {num}: ชื่อวัสดุ (name) ต้องไม่ว่าง")

    if errors:
        return False, errors, None

    cleaned = {
        "date": date,
        "type": type_,
        "doc_no": doc_no,
        "ref": sanitize(str(body.get("ref") or ""))[:200],
        "note": sanitize(str(body.get("note") or ""))[:500],
        "user_name": sanitize(str(body.get("user_name") or ""))[:100],
        "approver": sanitize(str(body.get("approver") or ""))[:100],
        "checker": sanitize(str(body.get("checker") or ""))[:100],
        "lines": [
            {
                "item_id": line.get("itemId", line.get("item_id")),
                "code": sanitize(str(line.get("code") or "")),
                "name": sanitize(str(line.get("name") or "")),
                "spec": sanitize(str(line.get("spec") or "-"))[:200],
                "unit": sanitize(str(line.get("unit") or ""))[:50],
                "qty": float(line.get("qty")),
                "price": float(line.get("price") or 0),
            }
            for line in lines
        ],
    }
    return True, [], cleaned
