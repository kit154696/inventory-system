"""Repository functions for the domain model — plain sqlite3, no ORM.

Ported business logic from server.js (routes for items/transactions/
balance/report/stockcard/dashboard/next-docno), adapted to SQLite.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import date as _date

from database.database import connect, transaction


class ItemInUseError(Exception):
    """Raised when deleting an item that is referenced by transaction_lines."""


class DuplicateCodeError(Exception):
    """Raised when an item code already exists."""


class InsufficientStockError(Exception):
    """Raised when an OUT transaction line would drive an item's balance negative."""


@dataclass
class Item:
    id: int
    code: str
    name: str
    spec: str
    cat_code: str
    cat_name: str
    unit: str
    min_qty: float
    location: str
    last_price: float
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Item":
        return cls(**{k: row[k] for k in row.keys()})


@dataclass
class TransactionLine:
    id: int | None
    item_id: int
    code: str
    name: str
    spec: str
    unit: str
    qty: float
    price: float
    tx_id: int | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "TransactionLine":
        return cls(**{k: row[k] for k in row.keys()})


@dataclass
class Transaction:
    id: int
    date: str
    type: str
    doc_no: str
    ref: str
    note: str
    user_name: str
    approver: str
    checker: str
    created_at: str
    lines: list[TransactionLine] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Transaction":
        data = {k: row[k] for k in row.keys()}
        return cls(**data, lines=[])


class CategoryRepo:
    @staticmethod
    def list_all() -> list[sqlite3.Row]:
        conn = connect()
        return conn.execute("SELECT code, name FROM categories ORDER BY code").fetchall()

    @staticmethod
    def get(code: str) -> sqlite3.Row | None:
        conn = connect()
        return conn.execute("SELECT code, name FROM categories WHERE code = ?", (code,)).fetchone()


class ItemRepo:
    @staticmethod
    def list(
        search: str | None = None,
        cat_code: str | None = None,
        page_size: int | None = None,
        offset: int | None = None,
    ) -> list[Item]:
        conn = connect()
        sql = "SELECT * FROM items WHERE 1=1"
        params: list = []
        if search:
            sql += " AND (code LIKE ? OR name LIKE ?)"
            like = f"%{search}%"
            params.extend([like, like])
        if cat_code:
            sql += " AND cat_code = ?"
            params.append(cat_code)
        sql += " ORDER BY code"
        if page_size is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([page_size, offset or 0])
        rows = conn.execute(sql, params).fetchall()
        return [Item.from_row(r) for r in rows]

    @staticmethod
    def count(search: str | None = None, cat_code: str | None = None) -> int:
        conn = connect()
        sql = "SELECT COUNT(*) as cnt FROM items WHERE 1=1"
        params: list = []
        if search:
            sql += " AND (code LIKE ? OR name LIKE ?)"
            like = f"%{search}%"
            params.extend([like, like])
        if cat_code:
            sql += " AND cat_code = ?"
            params.append(cat_code)
        return conn.execute(sql, params).fetchone()["cnt"]

    @staticmethod
    def get(item_id: int) -> Item | None:
        conn = connect()
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        return Item.from_row(row) if row else None

    @staticmethod
    def get_by_code(code: str) -> Item | None:
        conn = connect()
        row = conn.execute("SELECT * FROM items WHERE code = ?", (code,)).fetchone()
        return Item.from_row(row) if row else None

    @staticmethod
    def create(data: dict) -> int:
        with transaction() as conn:
            try:
                cur = conn.execute(
                    """INSERT INTO items
                       (code, name, spec, cat_code, cat_name, unit, min_qty, location, last_price)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        data["code"], data["name"], data.get("spec") or "-",
                        data["cat_code"], data["cat_name"], data["unit"],
                        data.get("min_qty", 0), data.get("location") or "กองพัสดุ",
                        data.get("last_price", 0),
                    ),
                )
            except sqlite3.IntegrityError as e:
                if "UNIQUE" in str(e):
                    raise DuplicateCodeError("รหัสวัสดุนี้มีอยู่แล้ว") from e
                raise
            return cur.lastrowid

    @staticmethod
    def update(item_id: int, data: dict) -> None:
        with transaction() as conn:
            try:
                conn.execute(
                    """UPDATE items SET code=?, name=?, spec=?, cat_code=?, cat_name=?,
                       unit=?, min_qty=?, location=?, last_price=?, updated_at=CURRENT_TIMESTAMP
                       WHERE id=?""",
                    (
                        data["code"], data["name"], data.get("spec") or "-",
                        data["cat_code"], data["cat_name"], data["unit"],
                        data.get("min_qty", 0), data.get("location") or "กองพัสดุ",
                        data.get("last_price", 0), item_id,
                    ),
                )
            except sqlite3.IntegrityError as e:
                if "UNIQUE" in str(e):
                    raise DuplicateCodeError("รหัสวัสดุนี้มีอยู่แล้ว") from e
                raise

    @staticmethod
    def delete(item_id: int) -> None:
        conn = connect()
        used = conn.execute(
            "SELECT COUNT(*) as cnt FROM transaction_lines WHERE item_id = ?", (item_id,)
        ).fetchone()["cnt"]
        if used > 0:
            raise ItemInUseError("ไม่สามารถลบได้ มีรายการเอกสารอ้างอิง")
        with transaction() as c:
            c.execute("DELETE FROM items WHERE id = ?", (item_id,))

    @staticmethod
    def balance(item_id: int, date_limit: str | None = None) -> float:
        conn = connect()
        sql = """
            SELECT COALESCE(SUM(CASE WHEN t.type='IN' THEN tl.qty ELSE 0 END), 0) -
                   COALESCE(SUM(CASE WHEN t.type='OUT' THEN tl.qty ELSE 0 END), 0) as balance
            FROM transaction_lines tl
            JOIN transactions t ON t.id = tl.tx_id
            WHERE tl.item_id = ?
        """
        params: list = [item_id]
        if date_limit:
            sql += " AND t.date <= ?"
            params.append(date_limit)
        row = conn.execute(sql, params).fetchone()
        return float(row["balance"])

    @staticmethod
    def balance_all(date_limit: str | None = None) -> dict[int, float]:
        conn = connect()
        sql = """
            SELECT tl.item_id,
                   COALESCE(SUM(CASE WHEN t.type='IN' THEN tl.qty ELSE 0 END), 0) -
                   COALESCE(SUM(CASE WHEN t.type='OUT' THEN tl.qty ELSE 0 END), 0) as balance
            FROM transaction_lines tl
            JOIN transactions t ON t.id = tl.tx_id
            WHERE 1=1
        """
        params: list = []
        if date_limit:
            sql += " AND t.date <= ?"
            params.append(date_limit)
        sql += " GROUP BY tl.item_id"
        rows = conn.execute(sql, params).fetchall()
        return {r["item_id"]: float(r["balance"]) for r in rows}


def _fiscal_year_bounds(for_date: str) -> tuple[str, str]:
    """Thai fiscal year: Oct 1 - Sep 30. Returns (fy_start, fy_end) as YYYY-MM-DD."""
    y, m, _ = (int(p) for p in for_date.split("-"))
    if m >= 10:
        return f"{y}-10-01", f"{y + 1}-09-30"
    return f"{y - 1}-10-01", f"{y}-09-30"


def _fiscal_year_be_short(for_date: str) -> str:
    """Last 2 digits of the Buddhist-Era fiscal year for a given Gregorian date."""
    y, m, _ = (int(p) for p in for_date.split("-"))
    fy_ad = y + 1 if m >= 10 else y
    return str(fy_ad + 543)[-2:]


class TransactionRepo:
    @staticmethod
    def list(
        type_: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Transaction]:
        conn = connect()
        sql = "SELECT * FROM transactions WHERE 1=1"
        params: list = []
        if type_:
            sql += " AND type = ?"
            params.append(type_)
        sql += " ORDER BY id DESC"
        if limit:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset or 0])
        rows = conn.execute(sql, params).fetchall()
        txs = [Transaction.from_row(r) for r in rows]
        for tx in txs:
            line_rows = conn.execute(
                "SELECT * FROM transaction_lines WHERE tx_id = ?", (tx.id,)
            ).fetchall()
            tx.lines = [TransactionLine.from_row(r) for r in line_rows]
        return txs

    @staticmethod
    def count(type_: str | None = None) -> int:
        conn = connect()
        sql = "SELECT COUNT(*) as cnt FROM transactions WHERE 1=1"
        params: list = []
        if type_:
            sql += " AND type = ?"
            params.append(type_)
        return conn.execute(sql, params).fetchone()["cnt"]

    @staticmethod
    def get(tx_id: int) -> Transaction | None:
        conn = connect()
        row = conn.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,)).fetchone()
        if not row:
            return None
        tx = Transaction.from_row(row)
        line_rows = conn.execute(
            "SELECT * FROM transaction_lines WHERE tx_id = ?", (tx_id,)
        ).fetchall()
        tx.lines = [TransactionLine.from_row(r) for r in line_rows]
        return tx

    @staticmethod
    def next_doc_no(type_: str, for_date: str) -> str:
        conn = connect()
        fy_start, fy_end = _fiscal_year_bounds(for_date)
        count = conn.execute(
            "SELECT COUNT(*) as cnt FROM transactions WHERE type = ? AND date >= ? AND date <= ?",
            (type_, fy_start, fy_end),
        ).fetchone()["cnt"]
        seq = str(count + 1).zfill(4)
        return f"{type_}-{seq}/{_fiscal_year_be_short(for_date)}"

    @staticmethod
    def create(header: dict, lines: list[dict]) -> int:
        """Insert a transaction + its lines in one write transaction.

        For OUT documents, each line is hard-blocked if it would drive the
        item's running balance negative (treated as a data-integrity rule
        for an official inventory-of-record, not just a warning).
        """
        with transaction() as conn:
            if header["type"] == "OUT":
                for line in lines:
                    bal = ItemRepo.balance(line["item_id"])
                    if line["qty"] > bal:
                        item = ItemRepo.get(line["item_id"])
                        name = item.name if item else line.get("name", "")
                        raise InsufficientStockError(
                            f'สินค้า "{name}" มีคงเหลือ {bal:g} แต่พยายามเบิก {line["qty"]:g}'
                        )

            cur = conn.execute(
                """INSERT INTO transactions
                   (date, type, doc_no, ref, note, user_name, approver, checker)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    header["date"], header["type"], header["doc_no"],
                    header.get("ref", ""), header.get("note", ""),
                    header.get("user_name", ""), header.get("approver", ""),
                    header.get("checker", ""),
                ),
            )
            tx_id = cur.lastrowid
            for line in lines:
                conn.execute(
                    """INSERT INTO transaction_lines
                       (tx_id, item_id, code, name, spec, unit, qty, price)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        tx_id, line["item_id"], line["code"], line["name"],
                        line.get("spec") or "-", line["unit"], line["qty"],
                        line.get("price", 0),
                    ),
                )
                if header["type"] == "IN" and line.get("price", 0) > 0:
                    conn.execute(
                        "UPDATE items SET last_price = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (line["price"], line["item_id"]),
                    )
            return tx_id

    @staticmethod
    def delete(tx_id: int) -> None:
        with transaction() as conn:
            conn.execute("DELETE FROM transaction_lines WHERE tx_id = ?", (tx_id,))
            conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))


class ReportRepo:
    @staticmethod
    def stock_report(cat_code: str | None = None, date_limit: str | None = None) -> list[dict]:
        items = ItemRepo.list(cat_code=cat_code)
        bal_map = ItemRepo.balance_all(date_limit=date_limit)
        report = []
        for item in items:
            bal = bal_map.get(item.id, 0.0)
            if bal <= 0:
                continue
            report.append({
                "id": item.id, "code": item.code, "name": item.name, "spec": item.spec,
                "cat_code": item.cat_code, "cat_name": item.cat_name, "unit": item.unit,
                "last_price": item.last_price, "balance": bal,
                "total_value": bal * item.last_price,
            })
        return report

    @staticmethod
    def stockcard(item_id: int) -> tuple[Item | None, list[dict]]:
        item = ItemRepo.get(item_id)
        if item is None:
            return None, []
        conn = connect()
        rows = conn.execute(
            """SELECT t.date, t.type, t.doc_no, t.ref, t.note, tl.qty, tl.price
               FROM transaction_lines tl
               JOIN transactions t ON t.id = tl.tx_id
               WHERE tl.item_id = ?
               ORDER BY t.date, t.id""",
            (item_id,),
        ).fetchall()
        balance = 0.0
        movements = []
        for row in rows:
            qty = float(row["qty"])
            balance += qty if row["type"] == "IN" else -qty
            movements.append({
                "date": row["date"], "type": row["type"], "doc_no": row["doc_no"],
                "ref": row["ref"], "note": row["note"], "qty": qty,
                "price": float(row["price"]), "balance": balance,
            })
        return item, movements

    @staticmethod
    def dashboard() -> dict:
        conn = connect()
        total_items = conn.execute("SELECT COUNT(*) as cnt FROM items").fetchone()["cnt"]

        rows = conn.execute("""
            SELECT i.id, i.name, i.cat_name, i.last_price, i.min_qty,
                   COALESCE(SUM(CASE WHEN t.type='IN' THEN tl.qty ELSE 0 END), 0) -
                   COALESCE(SUM(CASE WHEN t.type='OUT' THEN tl.qty ELSE 0 END), 0) as balance
            FROM items i
            LEFT JOIN transaction_lines tl ON tl.item_id = i.id
            LEFT JOIN transactions t ON t.id = tl.tx_id
            GROUP BY i.id, i.name, i.cat_name, i.last_price, i.min_qty
        """).fetchall()

        total_value = 0.0
        low_stock = []
        cat_value: dict[str, float] = {}
        for row in rows:
            bal = float(row["balance"])
            val = bal * row["last_price"]
            total_value += val
            cat_value[row["cat_name"]] = cat_value.get(row["cat_name"], 0.0) + val
            if bal <= row["min_qty"]:
                low_stock.append({"name": row["name"], "balance": bal, "min": row["min_qty"]})

        today = _date.today().isoformat()
        fy_start, _ = _fiscal_year_bounds(today)
        docs_this_year = conn.execute(
            "SELECT COUNT(*) as cnt FROM transactions WHERE date >= ?", (fy_start,)
        ).fetchone()["cnt"]

        return {
            "total_items": total_items,
            "total_value": total_value,
            "low_stock": low_stock,
            "docs_this_year": docs_this_year,
            "cat_value": cat_value,
        }

    @staticmethod
    def annual_summary(fiscal_year_be: int, cat_code: str | None = None) -> tuple[list[dict], dict]:
        """Thai fiscal-year (Oct 1 - Sep 30) receive/issue report.

        Ports server.js's buildReportSummary(): brought-forward balance is
        net movement strictly before the fiscal year start; received/issued
        are net movement within the fiscal year; items with zero movement
        across all three are skipped from the report entirely.
        """
        conn = connect()
        fy_ad = fiscal_year_be - 543
        fy_start = f"{fy_ad - 1}-10-01"
        fy_end = f"{fy_ad}-09-30"

        item_sql = "SELECT * FROM items WHERE 1=1"
        params: list = []
        if cat_code:
            item_sql += " AND cat_code = ?"
            params.append(cat_code)
        item_sql += " ORDER BY cat_code, code"
        items = conn.execute(item_sql, params).fetchall()

        bf_rows = conn.execute(
            """SELECT tl.item_id,
                      COALESCE(SUM(CASE WHEN t.type='IN'  THEN tl.qty ELSE 0 END), 0) as in_bf,
                      COALESCE(SUM(CASE WHEN t.type='OUT' THEN tl.qty ELSE 0 END), 0) as out_bf
               FROM transaction_lines tl
               JOIN transactions t ON t.id = tl.tx_id
               WHERE t.date < ?
               GROUP BY tl.item_id""",
            (fy_start,),
        ).fetchall()
        bf_map = {r["item_id"]: (float(r["in_bf"]), float(r["out_bf"])) for r in bf_rows}

        fy_rows = conn.execute(
            """SELECT tl.item_id,
                      COALESCE(SUM(CASE WHEN t.type='IN'  THEN tl.qty ELSE 0 END), 0) as received,
                      COALESCE(SUM(CASE WHEN t.type='OUT' THEN tl.qty ELSE 0 END), 0) as issued
               FROM transaction_lines tl
               JOIN transactions t ON t.id = tl.tx_id
               WHERE t.date >= ? AND t.date <= ?
               GROUP BY tl.item_id""",
            (fy_start, fy_end),
        ).fetchall()
        fy_map = {r["item_id"]: (float(r["received"]), float(r["issued"])) for r in fy_rows}

        rows: list[dict] = []
        no = 0
        tot_bf = tot_rec = tot_iss = tot_bal = 0.0
        for item in items:
            in_bf, out_bf = bf_map.get(item["id"], (0.0, 0.0))
            received, issued = fy_map.get(item["id"], (0.0, 0.0))
            brought_forward = in_bf - out_bf
            balance = brought_forward + received - issued

            if brought_forward == 0 and received == 0 and issued == 0:
                continue

            no += 1
            rows.append({
                "no": no, "cat_name": item["cat_name"], "name": item["name"],
                "unit": item["unit"], "brought_forward": brought_forward,
                "received": received, "issued": issued, "balance": balance,
            })
            tot_bf += brought_forward
            tot_rec += received
            tot_iss += issued
            tot_bal += balance

        totals = {
            "brought_forward": tot_bf, "received": tot_rec,
            "issued": tot_iss, "balance": tot_bal,
        }
        return rows, totals


class SettingsRepo:
    @staticmethod
    def get(key: str) -> str | None:
        conn = connect()
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    @staticmethod
    def set(key: str, value: str) -> None:
        with transaction() as conn:
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
