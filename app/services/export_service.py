"""Export the live database to ZIP / JSON / CSV formats."""
import csv
import json
import tempfile
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from database.database import connect
from database.models import CategoryRepo, ItemRepo, SettingsRepo, TransactionRepo
from services.backup_service import create_snapshot

APP_NAME = "StockApp"
APP_VERSION = "1.0.0"
FORMAT_VERSION = 1

README_TEXT = """StockApp Backup
================

This ZIP file is a backup of StockApp's data. It contains:
  - database.db   : a full copy of the SQLite database
  - metadata.json : information about this backup (app name, version, export date)

This backup does not reference any specific computer, user account, or
file path. It can be safely copied to another computer and imported from
there via Settings > Import Data in StockApp.

To restore: open StockApp on the target computer, go to
Settings > Backup / Export > Import Data, and select this ZIP file.
"""


def _current_schema_version() -> int:
    conn = connect()
    row = conn.execute("SELECT MAX(version) as v FROM schema_version").fetchone()
    return int(row["v"] or 0)


def _build_metadata() -> dict:
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "database_version": _current_schema_version(),
        "export_date": datetime.now().isoformat(),
        "format_version": FORMAT_VERSION,
    }


def export_zip(dest_path: Path) -> Path:
    dest_path = Path(dest_path)
    with tempfile.TemporaryDirectory() as tmpdir:
        db_snapshot = Path(tmpdir) / "database.db"
        create_snapshot(db_snapshot)

        metadata_path = Path(tmpdir) / "metadata.json"
        metadata_path.write_text(
            json.dumps(_build_metadata(), ensure_ascii=False, indent=2), encoding="utf-8"
        )

        readme_path = Path(tmpdir) / "README.txt"
        readme_path.write_text(README_TEXT, encoding="utf-8")

        with ZipFile(dest_path, "w", ZIP_DEFLATED) as zf:
            zf.write(db_snapshot, "database.db")
            zf.write(metadata_path, "metadata.json")
            zf.write(readme_path, "README.txt")

    return dest_path


def export_json(dest_path: Path) -> Path:
    dest_path = Path(dest_path)
    categories = [dict(row) for row in CategoryRepo.list_all()]
    items = [vars(i) for i in ItemRepo.list()]
    transactions = []
    for tx in TransactionRepo.list():
        tx_dict = vars(tx).copy()
        tx_dict["lines"] = [vars(line) for line in tx_dict.pop("lines")]
        transactions.append(tx_dict)
    settings_row = connect().execute("SELECT key, value FROM settings").fetchall()

    payload = {
        "app_name": APP_NAME,
        "format_version": FORMAT_VERSION,
        "export_date": datetime.now().isoformat(),
        "settings": [dict(row) for row in settings_row],
        "categories": categories,
        "items": items,
        "transactions": transactions,
    }
    dest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return dest_path


def export_csv(dest_dir: Path) -> list[Path]:
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    conn = connect()
    written: list[Path] = []

    tables = {
        "categories": ["code", "name"],
        "items": [
            "id", "code", "name", "spec", "cat_code", "cat_name", "unit",
            "min_qty", "location", "last_price", "created_at", "updated_at",
        ],
        "transactions": [
            "id", "date", "type", "doc_no", "ref", "note",
            "user_name", "approver", "checker", "created_at",
        ],
        "transaction_lines": [
            "id", "tx_id", "item_id", "code", "name", "spec", "unit", "qty", "price",
        ],
        "settings": ["key", "value"],
    }

    for table, columns in tables.items():
        out_path = dest_dir / f"{table}.csv"
        rows = conn.execute(f"SELECT {', '.join(columns)} FROM {table}").fetchall()
        with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow({col: row[col] for col in columns})
        written.append(out_path)

    return written
