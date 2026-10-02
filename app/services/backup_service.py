"""Snapshot / restore / retention for the live SQLite database.

Used both for manual "backup now", auto-backup-before-import, and as the
restore primitive for import rollback.
"""
import shutil
from datetime import datetime
from pathlib import Path

from database.database import connect, disconnect
from utils.paths import get_backup_dir, get_db_path

MAX_AUTO_BACKUPS = 10


def create_snapshot(dest_path: Path) -> Path:
    """Write a consistent single-file copy of the live DB to dest_path.

    Uses VACUUM INTO so an in-progress WAL is correctly folded into the
    snapshot rather than copying possibly-stale .db/.db-wal files directly.
    """
    dest_path = Path(dest_path)
    if dest_path.exists():
        dest_path.unlink()
    conn = connect()
    conn.execute("VACUUM INTO ?", (str(dest_path),))
    return dest_path


def create_auto_backup() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = get_backup_dir() / f"auto_backup_{timestamp}.db"
    create_snapshot(dest)
    _prune_old_backups()
    return dest


def list_backups() -> list[Path]:
    backups = sorted(get_backup_dir().glob("auto_backup_*.db"), reverse=True)
    return backups


def _prune_old_backups() -> None:
    backups = list_backups()
    for old in backups[MAX_AUTO_BACKUPS:]:
        try:
            old.unlink()
        except OSError:
            pass


def restore_db_file(backup_path: Path) -> None:
    """Replace the live database file with backup_path's contents.

    Closes the live connection first (checkpointing WAL), removes any
    stale WAL/SHM sidecar files, copies the backup over app.db, then
    reopens a fresh connection against the restored file.
    """
    backup_path = Path(backup_path)
    disconnect()

    db_path = get_db_path()
    for suffix in ("-wal", "-shm"):
        sidecar = Path(str(db_path) + suffix)
        if sidecar.exists():
            sidecar.unlink()

    shutil.copyfile(backup_path, db_path)
    connect()
