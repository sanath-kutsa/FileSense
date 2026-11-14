"""SQLite persistence for FileSense scan history."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .analyzer import build_summary
from .models import FileRecord

DEFAULT_DB_PATH = Path("instance") / "filesense.db"


def connect_database(database_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open the database, create its parent directory, and initialize tables."""
    path = Path(database_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            root_path TEXT NOT NULL,
            scanned_at TEXT NOT NULL,
            total_files INTEGER NOT NULL,
            total_bytes INTEGER NOT NULL,
            summary_json TEXT NOT NULL,
            error_count INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS scan_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            path TEXT NOT NULL,
            extension TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            modified_at TEXT NOT NULL,
            category TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_scan_files_scan_id
        ON scan_files(scan_id);
        """
    )
    connection.commit()
    return connection


def save_scan(
    root_path: str | Path,
    records: Iterable[FileRecord],
    errors: Iterable[str] = (),
    database_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    """Persist one scan and its file metadata, returning the scan ID."""
    record_list = list(records)
    error_list = list(errors)
    summary = build_summary(record_list)
    scanned_at = datetime.now(timezone.utc).isoformat()

    with connect_database(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO scans
                (root_path, scanned_at, total_files, total_bytes, summary_json, error_count)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(Path(root_path).expanduser().resolve()),
                scanned_at,
                summary["total_files"],
                summary["total_bytes"],
                json.dumps(summary, sort_keys=True),
                len(error_list),
            ),
        )
        scan_id = int(cursor.lastrowid)
        connection.executemany(
            """
            INSERT INTO scan_files
                (scan_id, name, path, extension, size_bytes, modified_at, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    scan_id,
                    record.name,
                    record.path,
                    record.extension,
                    record.size_bytes,
                    record.modified_at,
                    record.category,
                )
                for record in record_list
            ],
        )
    return scan_id


def list_scans(
    limit: int = 10,
    database_path: str | Path = DEFAULT_DB_PATH,
) -> list[dict]:
    """Return recent scan summaries, newest first."""
    if limit < 1:
        raise ValueError("limit must be at least 1.")
    path = Path(database_path).expanduser()
    if not path.exists():
        return []

    with connect_database(path) as connection:
        rows = connection.execute(
            """
            SELECT id, root_path, scanned_at, total_files, total_bytes,
                   summary_json, error_count
            FROM scans
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    results = []
    for row in rows:
        item = dict(row)
        item["summary"] = json.loads(item.pop("summary_json"))
        results.append(item)
    return results
