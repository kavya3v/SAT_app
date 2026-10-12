"""Back up and import one family's SQLite progress into empty PostgreSQL tables."""

import argparse
import sqlite3
from pathlib import Path
from uuid import uuid4

from sat_prep.storage.configuration import database_target, private_settings
from sat_prep.storage.database import apply_postgres_schema, connect, is_postgres

TABLES = {
    'profile': ('id', 'name', 'target_minutes'),
    'sessions': ('id', 'started_at', 'completed_at', 'duration_seconds', 'completed'),
    'answers': ('id', 'session_id', 'question_id', 'skill', 'module', 'selected_answer', 'is_correct', 'answered_at'),
    'preparation_plan': ('id', 'graduation_year', 'target_score'),
    'score_reports': ('id', 'test_type', 'test_date', 'reading_writing', 'math'),
}
DEFAULTS = {
    'profile': [{'id': 1, 'name': 'Student', 'target_minutes': 20}],
    'preparation_plan': [{'id': 1, 'graduation_year': 2030, 'target_score': 1400}],
}


def read_snapshot(source, make_backup=True):
    source = Path(source).resolve()
    if not source.is_file():
        raise ValueError('The source SQLite database does not exist.')
    backup = None
    with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute('BEGIN')
        if connection.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
            raise ValueError('The source database failed its integrity check.')
        if connection.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('The source database contains broken session/answer relationships.')
        available = {row['name'] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'profile', 'sessions', 'answers'} <= available:
            raise ValueError('The source is not a SAT app progress database.')
        snapshot = {}
        for table, columns in TABLES.items():
            if table not in available:
                # Older local apps predate the score dashboard. Supply its defaults
                # in the import snapshot, without changing the original file.
                snapshot[table] = [dict(row) for row in DEFAULTS.get(table, [])]
                continue
            # Identifiers come exclusively from the fixed whitelist above.
            rows = connection.execute(f"SELECT {', '.join(columns)} FROM {table} ORDER BY id").fetchall()
            snapshot[table] = [dict(row) for row in rows]
        if len(snapshot['profile']) != 1 or len(snapshot['preparation_plan']) != 1:
            raise ValueError('The source must have one family profile and one preparation plan.')
        if make_backup:
            backup = source.with_name(f'{source.stem}.before-cloud-{uuid4().hex[:12]}.db')
            with sqlite3.connect(backup) as destination:
                connection.backup(destination)
        connection.rollback()
    return snapshot, backup


def import_snapshot(connection, snapshot):
    """Import and verify inside a caller-owned transaction; never overwrite data."""
    for table, columns in TABLES.items():
        current = [dict(row) for row in connection.execute(
            f"SELECT {', '.join(columns)} FROM {table} ORDER BY id"
        ).fetchall()]
        if current and current != DEFAULTS.get(table):
            raise ValueError('The destination already contains family progress; import refused.')
    for table, columns in TABLES.items():
        if table in DEFAULTS:
            connection.execute(f'DELETE FROM {table}')
        placeholders = ', '.join('?' for _ in columns)
        for row in snapshot[table]:
            connection.execute(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                               tuple(row[column] for column in columns))
    counts = {}
    for table, columns in TABLES.items():
        actual = [dict(row) for row in connection.execute(
            f"SELECT {', '.join(columns)} FROM {table} ORDER BY id"
        ).fetchall()]
        if actual != snapshot[table]:
            raise ValueError('Imported data did not match the source; transaction will roll back.')
        counts[table] = len(actual)
    return counts


def reset_sequences(connection, snapshot):
    for table in ('sessions', 'answers', 'score_reports'):
        maximum = max((row['id'] for row in snapshot[table]), default=0)
        connection.execute("SELECT setval(pg_get_serial_sequence(?, 'id'), ?, ?)",
                           (table, max(1, maximum), maximum > 0))


def migrate(source, target):
    if not is_postgres(target):
        raise ValueError('The migration destination must be PostgreSQL.')
    database_target(None, {'SAT_DATABASE_URL': target})
    snapshot, backup = read_snapshot(source)
    with connect(target) as connection:
        apply_postgres_schema(connection)
        connection.execute('LOCK TABLE profile, sessions, answers, preparation_plan, score_reports IN ACCESS EXCLUSIVE MODE')
        counts = import_snapshot(connection, snapshot)
        reset_sequences(connection, snapshot)
    return counts, backup


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('data/sat_prep.db'))
    parser.add_argument('--secrets-file', type=Path, default=Path('.streamlit/secrets.toml'))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true', help='Validate and count local data without changing databases.')
    mode.add_argument('--apply', action='store_true', help='Back up and import local data into the configured empty cloud database.')
    mode.add_argument('--check', action='store_true', help='Check cloud connectivity, initialize its schema, and show row counts.')
    args = parser.parse_args(argv)
    try:
        if args.dry_run:
            snapshot, _ = read_snapshot(args.source, make_backup=False)
            print('Local snapshot validated. No data changed.')
            for table, rows in snapshot.items():
                print(f'{table}: {len(rows)} rows')
            return 0
        target = database_target(None, private_settings(args.secrets_file))
        if not is_postgres(target):
            raise ValueError('Configure SAT_DATABASE_URL privately before connecting.')
        if args.check:
            with connect(target) as connection:
                apply_postgres_schema(connection)
                counts = {table: connection.execute(f'SELECT COUNT(*) AS n FROM {table}').fetchone()['n']
                          for table in TABLES}
            print('Cloud connection and schema verified.')
        else:
            counts, backup = migrate(args.source, target)
            print(f'Import verified and committed. Local backup: {backup.name}')
        for table, count in counts.items():
            print(f'{table}: {count} rows')
        return 0
    except Exception:
        # Do not print exceptions: drivers and TOML parsers can include secrets.
        print('Operation failed. Check the private connection setting, source integrity, and that the cloud destination is empty. No partial import was committed. Credentials are not displayed.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
