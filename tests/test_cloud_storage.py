from datetime import datetime

import pytest

from sat_prep.storage import database, repository
from sat_prep.storage.configuration import database_target


def test_cloud_configuration_is_explicit_and_does_not_fall_back(tmp_path):
    default = tmp_path / 'local.db'
    assert database_target(default, {}) == default
    url = 'postgresql://test:example@localhost/family?sslmode=require'
    assert database_target(default, {'SAT_DATABASE_URL': url}) == url
    for value in ('', 'sqlite://local', 'https://example.com', 'postgresql://'):
        with pytest.raises(ValueError):
            database_target(default, {'SAT_DATABASE_URL': value})
    with pytest.raises(ValueError):
        database_target(default, {'SAT_DATABASE_URL': 'postgresql://test:example@cloud.example/family?sslmode=disable'})


def test_postgres_adapter_keeps_user_values_parameterized():
    class RawConnection:
        def execute(self, query, params=None):
            self.query, self.params = query, params
            return self
    raw = RawConnection()
    adapter = database.PostgresConnection(raw)
    adapter.execute('UPDATE profile SET name=? WHERE id=?', ('Why? 100%', 1))
    assert raw.query == 'UPDATE profile SET name=%s WHERE id=%s'
    assert raw.params == ('Why? 100%', 1)


def test_failed_connection_rolls_back_sqlite(tmp_path):
    db = tmp_path / 'local.db'
    database.initialize(db)
    with pytest.raises(RuntimeError):
        with database.connect(db) as connection:
            connection.execute("UPDATE profile SET name='Changed' WHERE id=1")
            raise RuntimeError('cancel')
    assert repository.get_profile(db)['name'] == 'Student'
    first = repository.start_session(db, datetime(2026, 1, 1))
    second = repository.start_session(db, datetime(2026, 1, 2))
    assert second > first


def test_postgres_connection_commits_and_rolls_back(monkeypatch):
    import psycopg
    from psycopg.rows import dict_row

    calls = []
    class Raw:
        def __enter__(self):
            return self
        def __exit__(self, error_type, error, traceback):
            calls.append('rollback' if error_type else 'commit')
        def execute(self, query, params=None):
            calls.append((query, params))

    def open_connection(url, **options):
        assert options['row_factory'] is dict_row
        assert options['connect_timeout'] == 10
        assert options['sslmode'] == 'require'
        return Raw()

    monkeypatch.setattr(psycopg, 'connect', open_connection)
    url = 'postgresql://test:example@cloud.example/family'
    with database.connect(url) as connection:
        connection.execute('SELECT ?', (1,))
    with pytest.raises(RuntimeError):
        with database.connect(url):
            raise RuntimeError('abort')
    assert calls == [('SELECT %s', (1,)), 'commit', 'rollback']
