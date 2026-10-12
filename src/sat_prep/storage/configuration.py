"""Resolve database settings without logging credentials."""

import os
import tomllib
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


def database_target(default, values):
    if 'SAT_DATABASE_URL' not in values:
        return default
    value = values['SAT_DATABASE_URL']
    if not isinstance(value, str) or not value.strip():
        raise ValueError('SAT_DATABASE_URL must be a PostgreSQL connection URL.')
    value = value.strip()
    try:
        parsed = urlsplit(value)
        valid = parsed.scheme in ('postgres', 'postgresql') and parsed.hostname and parsed.path.strip('/')
        sslmode = parse_qs(parsed.query).get('sslmode', ['require'])
        if parsed.hostname not in ('localhost', '127.0.0.1', '::1'):
            valid = valid and len(sslmode) == 1 and sslmode[0] in ('require', 'verify-ca', 'verify-full')
        if not valid:
            raise ValueError
    except ValueError:
        raise ValueError('Use a valid PostgreSQL URL with encrypted cloud connections.') from None
    return value


def private_settings(secrets_path=None, environ=None):
    """CLI settings: environment wins, otherwise read the ignored TOML file."""
    environment = os.environ if environ is None else environ
    if 'SAT_DATABASE_URL' in environment:
        return {'SAT_DATABASE_URL': environment['SAT_DATABASE_URL']}
    path = Path(secrets_path or '.streamlit/secrets.toml')
    if path.is_file():
        with path.open('rb') as file:
            return tomllib.load(file)
    return {}
