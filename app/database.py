from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from app.config import settings


def ensure_database_dir() -> None:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def db_connection() -> Iterator[sqlite3.Connection]:
    ensure_database_dir()
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with db_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT '学习材料',
                keywords TEXT NOT NULL DEFAULT '[]',
                summary TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                published_at TEXT NOT NULL DEFAULT '',
                is_weekly INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                keywords TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT '待完成',
                due_at TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS activity_signups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_name TEXT NOT NULL,
                user_id TEXT NOT NULL,
                user_name TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(activity_name, user_id)
            );

            CREATE TABLE IF NOT EXISTS interaction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                chat_id TEXT NOT NULL DEFAULT '',
                command TEXT NOT NULL DEFAULT '',
                raw_text TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        _ensure_column(conn, "materials", "external_source", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "materials", "external_id", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "materials", "synced_at", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "tasks", "external_source", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "tasks", "external_id", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "tasks", "synced_at", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "tasks", "last_reminded_at", "TEXT NOT NULL DEFAULT ''")
        conn.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_materials_external
            ON materials(external_source, external_id);

            CREATE INDEX IF NOT EXISTS idx_tasks_external
            ON tasks(external_source, external_id);
            """
        )


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for key in ("keywords",):
        if key in data and isinstance(data[key], str):
            try:
                data[key] = json.loads(data[key])
            except json.JSONDecodeError:
                data[key] = []
    return data


def database_exists(path: Path | None = None) -> bool:
    return (path or settings.database_path).exists()
