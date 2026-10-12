"""SQLite and PostgreSQL schema and transactional connection helpers."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import parse_qs, urlsplit

from sat_prep.storage.configuration import database_target


def is_postgres(target):
    return isinstance(target, str) and target.startswith(('postgresql://', 'postgres://'))


class PostgresConnection:
    """Adapt the repository's fixed qmark queries to psycopg's parameter style.

    Only application-owned SQL templates pass through here. User values always
    remain separate parameters; they are never interpolated or transformed.
    """
    def __init__(self, raw):
        self.raw = raw

    def execute(self, query, params=None):
        if params is None:
            return self.raw.execute(query)
        return self.raw.execute(query.replace('?', '%s'), params)


@contextmanager
def connect(db_path: str | Path) -> Iterator[sqlite3.Connection]:
    if is_postgres(db_path):
        import psycopg
        from psycopg.rows import dict_row

        database_target(None, {'SAT_DATABASE_URL': db_path})
        options = {'row_factory': dict_row, 'connect_timeout': 10, 'prepare_threshold': None}
        if 'sslmode' not in parse_qs(urlsplit(db_path).query):
            options['sslmode'] = 'require'
        with psycopg.connect(db_path, **options) as connection:
            # psycopg commits on normal exit and rolls back on exception.
            yield PostgresConnection(connection)
        return
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
    if is_postgres(db_path):
        with connect(db_path) as connection:
            apply_postgres_schema(connection)
        return
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


def apply_postgres_schema(connection):
    """Apply schema version 1 transactionally, serialized across app instances."""
    connection.execute('SELECT pg_advisory_xact_lock(72462191)')
    connection.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)')
    versions = {row['version'] for row in connection.execute('SELECT version FROM schema_migrations').fetchall()}
    if versions - {1}:
        raise ValueError('The database schema is newer than this app supports.')
    if 1 not in versions:
        sql = (Path(__file__).parent / 'migrations' / '001_postgresql.sql').read_text(encoding='utf-8')
        for statement in sql.split(';'):
            if statement.strip():
                connection.execute(statement)
        connection.execute('INSERT INTO schema_migrations (version) VALUES (1)')
