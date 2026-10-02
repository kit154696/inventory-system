"""AppData path resolution.

The database must never live next to the .exe or use a machine-specific
absolute path (Windows permission issues + backups become unportable).
Everything is resolved dynamically from the OS-provided APPDATA/home dir.
"""
import os
from pathlib import Path

APP_NAME = "StockApp"


def get_app_data_dir() -> Path:
    base = os.getenv("APPDATA") or str(Path.home())
    d = Path(base) / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_data_dir() -> Path:
    d = get_app_data_dir() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_db_path() -> Path:
    return get_data_dir() / "app.db"


def get_backup_dir() -> Path:
    d = get_app_data_dir() / "backup"
    d.mkdir(parents=True, exist_ok=True)
    return d
