"""Live tests require a separate test database, never the family connection."""

from datetime import date, datetime
import os
from uuid import uuid4

import pytest

from sat_prep.storage import repository
from sat_prep.storage.configuration import database_target
from sat_prep.storage.database import connect, initialize
from sat_prep.storage.migrate import migrate


@pytest.fixture
def postgres_target(monkeypatch):
    url = os.environ.get('SAT_TEST_DATABASE_URL')
    if not url:
        pytest.skip('No separate SAT_TEST_DATABASE_URL configured; live PostgreSQL test not run.')
    import psycopg
    from psycopg import sql

    database_target(None, {'SAT_DATABASE_URL': url})
    schema = 'sat_test_' + uuid4().hex
    with psycopg.connect(url, autocommit=True) as admin:
        admin.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    original = psycopg.connect

    def scoped_connection(dsn, **kwargs):
        if dsn == url:
            kwargs['options'] = f'-c search_path={schema}'
        return original(dsn, **kwargs)

    monkeypatch.setattr(psycopg, 'connect', scoped_connection)
    try:
        yield url
    finally:
        with original(url, autocommit=True) as admin:
            admin.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def test_live_postgres_migration_and_repository(postgres_target, tmp_path):
    source = tmp_path / 'source.db'
    initialize(source)
    started = datetime(2026, 1, 1)
    repository.save_profile(source, 'Migration test')
    repository.save_preparation_plan(source, 2030, 1450)
    session = repository.start_session(source, started)
    repository.save_answer(source, session, {'Question_ID': 'Q1', 'Module': 'Math', 'Skill': 'Algebra'}, 'A', True, started)
    repository.complete_session(source, session, started, 1200)
    repository.save_score(source, 'SAT', date(2026, 1, 1), 600, 650)
    counts, backup = migrate(source, postgres_target)
    assert backup.is_file() and counts['answers'] == 1
    initialize(postgres_target)
    initialize(postgres_target)
    assert repository.get_profile(postgres_target)['name'] == 'Migration test'
    assert repository.get_preparation_plan(postgres_target)['target_score'] == 1450
    assert repository.get_answer_history(postgres_target)[0]['session_id'] == session
    assert repository.completed_session_dates(postgres_target) == [date(2026, 1, 1)]
    assert repository.start_session(postgres_target, datetime(2026, 1, 2)) > session
    repository.save_score(postgres_target, 'SAT', date(2026, 1, 2), 610, 660)
    scores = repository.get_scores(postgres_target)
    assert scores[0]['id'] > scores[1]['id']
    repository.delete_score(postgres_target, scores[0]['id'])
    with pytest.raises(ValueError, match='already contains'):
        migrate(source, postgres_target)
    assert len(repository.get_scores(postgres_target)) == 1
    with connect(postgres_target) as connection:
        assert connection.execute('SELECT version FROM schema_migrations').fetchone()['version'] == 1
