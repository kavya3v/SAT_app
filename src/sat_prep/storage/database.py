"""SQLite schema and connection helpers."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def connect(db_path: str | Path) -> Iterator[sqlite3.Connection]:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize(db_path: str | Path) -> None:
    with connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT NOT NULL DEFAULT 'Student',
                target_minutes INTEGER NOT NULL DEFAULT 20
            );
            INSERT OR IGNORE INTO profile (id, name, target_minutes) VALUES (1, 'Student', 20);
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                duration_seconds INTEGER NOT NULL DEFAULT 0,
                completed INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id),
                question_id TEXT NOT NULL,
                skill TEXT NOT NULL,
                module TEXT NOT NULL,
                selected_answer TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                answered_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS preparation_plan (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                graduation_year INTEGER NOT NULL DEFAULT 2030,
                target_score INTEGER NOT NULL DEFAULT 1400
            );
            INSERT OR IGNORE INTO preparation_plan (id) VALUES (1);
            CREATE TABLE IF NOT EXISTS score_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_type TEXT NOT NULL,
                test_date TEXT NOT NULL,
                reading_writing INTEGER NOT NULL,
                math INTEGER NOT NULL
            );
            """
        )
