# Persistent Cloud Storage Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan inline, task by task.

**Goal:** Add persistent PostgreSQL family storage and a safe SQLite import.

**Architecture:** Retain pages and repository APIs. Select SQLite or PostgreSQL at the connection boundary; load a versioned PostgreSQL schema. Add a separate migration CLI with atomic import and verification.

**Tech Stack:** Streamlit, SQLite, psycopg 3, Neon PostgreSQL, pytest.

**Spec:** ../specs/2026-10-11-cloud-storage-design.md

## Global constraints

- One shared student; no multi-user authentication in this change.
- No cloud secret in source, output, command-line arguments, or Git.
- SQLite remains the default; configured cloud failures never fall back.
- Preserve local data and reject nonempty migration destinations.

## Review focus

- Placeholder conversion must preserve question marks in user values.
- Invalid URLs and secrets must not appear in UI errors.
- Migration must reject foreign-key corruption and retain existing target data.
- Imports must roll back entirely if verification fails.
- New IDs after import must not collide with imported IDs.

## Tasks

- [x] Add storage/configuration tests and observe failure; implement backend selection, PostgreSQL adapter, schema, and portable generated IDs.
- [x] Add migration tests and observe failure; implement backup, empty-target guard, transaction, row verification, and sequence reset.
- [x] Add optional live PostgreSQL tests and Streamlit configuration coverage. Run the full regression suite. Live test remains skipped without a separate connection.
- [x] Document Neon setup, secrets, import, restart verification, and remaining live setup requirements; update the architecture diagram.
