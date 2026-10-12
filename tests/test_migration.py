from datetime import datetime
import sqlite3

import pytest

from sat_prep.storage.database import connect, initialize
from sat_prep.storage import repository
from sat_prep.storage.migrate import read_snapshot, import_snapshot, main


def populated_source(path):
    initialize(path)
    repository.save_profile(path, 'Family student')
    repository.save_preparation_plan(path, 2030, 1450)
    started = datetime(2026, 1, 1)
    session = repository.start_session(path, started)
    repository.save_answer(path, session, {'Question_ID': 'Q1', 'Module': 'Math', 'Skill': 'Algebra'}, 'B', True, started)
    repository.complete_session(path, session, started, 1200)
    repository.save_score(path, 'SAT', started.date(), 600, 650)


def test_snapshot_backup_and_import_preserve_all_rows(tmp_path):
    source, destination = tmp_path / 'source.db', tmp_path / 'destination.db'
    populated_source(source)
    snapshot, backup = read_snapshot(source)
    assert backup.is_file()
    backup_snapshot, _ = read_snapshot(backup, make_backup=False)
    assert snapshot == backup_snapshot
    initialize(destination)
    with connect(destination) as connection:
        counts = import_snapshot(connection, snapshot)
    assert counts == {'profile': 1, 'sessions': 1, 'answers': 1, 'preparation_plan': 1, 'score_reports': 1}
    assert repository.get_profile(destination)['name'] == 'Family student'
    assert repository.get_answer_history(destination)[0]['session_id'] == 1
    assert repository.get_scores(destination)[0]['reading_writing'] == 600
    assert repository.start_session(destination, datetime(2026, 1, 2)) > 1


def test_nonempty_destination_is_not_overwritten(tmp_path):
    source, destination = tmp_path / 'source.db', tmp_path / 'destination.db'
    populated_source(source)
    snapshot, _ = read_snapshot(source, make_backup=False)
    initialize(destination)
    repository.save_profile(destination, 'Keep me')
    with pytest.raises(ValueError, match='already contains'):
        with connect(destination) as connection:
            import_snapshot(connection, snapshot)
    assert repository.get_profile(destination)['name'] == 'Keep me'


def test_failed_import_rolls_back_every_table(tmp_path):
    source, destination = tmp_path / 'source.db', tmp_path / 'destination.db'
    populated_source(source)
    snapshot, _ = read_snapshot(source, make_backup=False)
    snapshot['answers'][0]['session_id'] = 999
    initialize(destination)
    with pytest.raises(sqlite3.IntegrityError):
        with connect(destination) as connection:
            import_snapshot(connection, snapshot)
    assert repository.get_profile(destination)['name'] == 'Student'
    assert repository.get_answer_history(destination) == []
    with connect(destination) as connection:
        assert connection.execute('SELECT COUNT(*) AS n FROM sessions').fetchone()['n'] == 0


def test_missing_source_is_not_created(tmp_path):
    missing = tmp_path / 'missing.db'
    with pytest.raises(ValueError, match='does not exist'):
        read_snapshot(missing)
    assert not missing.exists()


def test_cli_does_not_echo_a_bad_connection_secret(tmp_path, monkeypatch, capsys):
    secret = 'do-not-print-this-password'
    monkeypatch.setenv('SAT_DATABASE_URL', f'https://{secret}@example.com/db')
    assert main(['--check']) == 1
    assert secret not in capsys.readouterr().out


def test_dry_run_needs_no_cloud_connection_and_changes_nothing(tmp_path, monkeypatch, capsys):
    source = tmp_path / 'source.db'
    populated_source(source)
    monkeypatch.delenv('SAT_DATABASE_URL', raising=False)
    before = source.read_bytes()
    assert main(['--source', str(source), '--dry-run']) == 0
    assert 'sessions: 1 rows' in capsys.readouterr().out
    assert source.read_bytes() == before


def test_snapshot_accepts_database_from_before_score_dashboard(tmp_path):
    source = tmp_path / 'legacy.db'
    initialize(source)
    with sqlite3.connect(source) as connection:
        connection.execute('DROP TABLE score_reports')
        connection.execute('DROP TABLE preparation_plan')
    snapshot, _ = read_snapshot(source, make_backup=False)
    assert snapshot['score_reports'] == []
    assert snapshot['preparation_plan'] == [{'id': 1, 'graduation_year': 2030, 'target_score': 1400}]
