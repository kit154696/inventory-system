"""Import a StockApp backup ZIP: validate, preview, then swap in the DB file.

Two-phase API:
  inspect_backup_zip() -> validate + count (steps 1-5, read-only, safe to
                           call repeatedly for a UI preview)
  import_backup_zip()  -> actually perform the import (steps 7-10), only
                           after the caller has shown the preview and the
                           user confirmed (step 6 lives in the UI dialog)
"""
import json
import sqlite3
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from database import migrations
from database.database import connect
from services.backup_service import create_auto_backup, restore_db_file
from services.export_service import APP_NAME, FORMAT_VERSION

REQUIRED_TABLES = {
    "items", "transactions", "transaction_lines",
    "categories", "settings", "schema_version",
}
SUPPORTED_FORMAT_VERSIONS = {1}


@dataclass
class InspectResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    app_name: str | None = None
    export_date: str | None = None
    format_version: int | None = None
    counts: dict[str, int] = field(default_factory=dict)


@dataclass
class ImportResult:
    ok: bool
    error: str | None = None


def inspect_backup_zip(path: Path) -> InspectResult:
    path = Path(path)

    try:
        zf = ZipFile(path, "r")
    except (BadZipFile, FileNotFoundError, OSError):
        return InspectResult(ok=False, errors=["ไม่สามารถเปิดไฟล์นี้ได้ หรือไม่ใช่ไฟล์ ZIP ที่ถูกต้อง"])

    with zf:
        names = set(zf.namelist())
        if "database.db" not in names or "metadata.json" not in names:
            return InspectResult(
                ok=False,
                errors=["ไม่ใช่ไฟล์ Backup ของโปรแกรมนี้ (ไม่พบ database.db หรือ metadata.json)"],
            )

        try:
            metadata = json.loads(zf.read("metadata.json").decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return InspectResult(ok=False, errors=["ไฟล์ metadata.json เสียหายหรืออ่านไม่ได้"])

        app_name = metadata.get("app_name")
        format_version = metadata.get("format_version")
        export_date = metadata.get("export_date")

        errors: list[str] = []
        if app_name != APP_NAME:
            errors.append(f'ไฟล์นี้ไม่ใช่ Backup ของ {APP_NAME} (พบ app_name="{app_name}")')
        if format_version not in SUPPORTED_FORMAT_VERSIONS:
            errors.append(f"format_version ของไฟล์นี้ ({format_version}) ไม่รองรับ")
        if errors:
            return InspectResult(
                ok=False, errors=errors, app_name=app_name,
                export_date=export_date, format_version=format_version,
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "database.db"
            db_path.write_bytes(zf.read("database.db"))

            temp_conn = sqlite3.connect(str(db_path))
            temp_conn.row_factory = sqlite3.Row

            try:
                table_rows = temp_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                table_names = {row["name"] for row in table_rows}
                missing = REQUIRED_TABLES - table_names
                if missing:
                    return InspectResult(
                        ok=False,
                        errors=[f"ไฟล์ฐานข้อมูลไม่ถูกต้อง ไม่พบตาราง: {', '.join(sorted(missing))}"],
                    )

                integrity = temp_conn.execute("PRAGMA integrity_check;").fetchall()
                if not (len(integrity) == 1 and integrity[0][0] == "ok"):
                    return InspectResult(ok=False, errors=["ฐานข้อมูลในไฟล์ Backup เสียหาย (integrity_check ล้มเหลว)"])

                fk_violations = temp_conn.execute("PRAGMA foreign_key_check;").fetchall()
                if fk_violations:
                    return InspectResult(ok=False, errors=["ฐานข้อมูลในไฟล์ Backup มีข้อมูลอ้างอิงไม่ถูกต้อง (foreign key)"])

                counts = {
                    "items": temp_conn.execute("SELECT COUNT(*) FROM items").fetchone()[0],
                    "transactions": temp_conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0],
                    "categories": temp_conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0],
                }
            except sqlite3.DatabaseError:
                return InspectResult(ok=False, errors=["ไฟล์ database.db ในไฟล์ Backup ไม่ใช่ฐานข้อมูล SQLite ที่ถูกต้อง"])
            finally:
                temp_conn.close()

        return InspectResult(
            ok=True, app_name=app_name, export_date=export_date,
            format_version=format_version, counts=counts,
        )


def import_backup_zip(path: Path) -> ImportResult:
    """Perform the actual import. Caller must have already shown the user
    the result of inspect_backup_zip() and obtained confirmation.
    """
    path = Path(path)
    pre_import_backup = None
    try:
        pre_import_backup = create_auto_backup()

        with ZipFile(path, "r") as zf:
            with tempfile.TemporaryDirectory() as tmpdir:
                extracted_db = Path(tmpdir) / "database.db"
                extracted_db.write_bytes(zf.read("database.db"))
                restore_db_file(extracted_db)

        conn = connect()
        migrations.run_migrations(conn)

        integrity = conn.execute("PRAGMA integrity_check;").fetchall()
        if not (len(integrity) == 1 and integrity[0][0] == "ok"):
            raise RuntimeError("ฐานข้อมูลหลัง Import เสียหาย (integrity_check ล้มเหลว)")

        return ImportResult(ok=True)

    except Exception as e:
        if pre_import_backup is not None:
            try:
                restore_db_file(pre_import_backup)
            except Exception:
                pass
        return ImportResult(ok=False, error=str(e))
