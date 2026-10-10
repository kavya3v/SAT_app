"""Persistence operations for profile, sessions, and answers."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from sat_prep.storage.database import connect


def get_profile(db_path: str | Path) -> dict[str, object]:
    with connect(db_path) as connection:
        row = connection.execute("SELECT name, target_minutes FROM profile WHERE id=1").fetchone()
    return dict(row)


def save_profile(db_path: str | Path, name: str) -> None:
    with connect(db_path) as connection:
        connection.execute("UPDATE profile SET name=? WHERE id=1", (name.strip() or "Student",))


def start_session(db_path: str | Path, started_at: datetime) -> int:
    with connect(db_path) as connection:
        cursor = connection.execute("INSERT INTO sessions (started_at) VALUES (?)", (started_at.isoformat(),))
        return int(cursor.lastrowid)


def save_answer(
    db_path: str | Path, session_id: int, question: dict[str, str],
    selected_answer: str, correct: bool, answered_at: datetime,
) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """INSERT INTO answers
            (session_id, question_id, skill, module, selected_answer, is_correct, answered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (session_id, question["Question_ID"], question["Skill"], question["Module"],
             selected_answer, int(correct), answered_at.isoformat()),
        )


def complete_session(db_path: str | Path, session_id: int, completed_at: datetime, duration: int) -> None:
    with connect(db_path) as connection:
        connection.execute(
            "UPDATE sessions SET completed_at=?, duration_seconds=?, completed=1 WHERE id=?",
            (completed_at.isoformat(), duration, session_id),
        )


def abandon_session(db_path: str | Path, session_id: int, ended_at: datetime, duration: int) -> None:
    """Record an unfinished session without counting it toward a streak."""
    with connect(db_path) as connection:
        connection.execute(
            "UPDATE sessions SET completed_at=?, duration_seconds=?, completed=0 WHERE id=?",
            (ended_at.isoformat(), duration, session_id),
        )


def completed_session_dates(db_path: str | Path) -> list[date]:
    with connect(db_path) as connection:
        rows = connection.execute("SELECT completed_at FROM sessions WHERE completed=1").fetchall()
    return [datetime.fromisoformat(row["completed_at"]).date() for row in rows]


def get_answer_history(db_path: str | Path) -> list[dict[str, object]]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """SELECT a.*, s.completed, s.started_at FROM answers a
            JOIN sessions s ON s.id=a.session_id ORDER BY a.answered_at DESC"""
        ).fetchall()
    return [dict(row) for row in rows]


def get_mistakes(db_path: str | Path) -> list[dict[str, object]]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """SELECT question_id, skill, module, selected_answer, answered_at
            FROM answers WHERE is_correct=0 ORDER BY answered_at DESC"""
        ).fetchall()
    return [dict(row) for row in rows]
