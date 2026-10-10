"""Load and filter the CSV question bank."""

from __future__ import annotations

import csv
from pathlib import Path

REQUIRED_COLUMNS = {
    "Question_ID", "Module", "Domain", "Skill", "Difficulty", "Question",
    "Choice_A", "Choice_B", "Choice_C", "Choice_D", "Correct_Answer",
    "Correct_Text", "Explanation",
}


def load_questions(path: str | Path) -> list[dict[str, str]]:
    """Read questions from CSV and reject malformed or duplicate records."""
    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        headers = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - headers
        if missing:
            raise ValueError(f"Question bank is missing columns: {', '.join(sorted(missing))}")
        questions = [
            {key: (value or "").strip() for key, value in row.items() if key}
            for row in reader
        ]

    seen_ids: set[str] = set()
    for row_number, question in enumerate(questions, start=2):
        question_id = question["Question_ID"]
        if not question_id:
            raise ValueError(f"Question_ID is blank on CSV row {row_number}")
        if question_id in seen_ids:
            raise ValueError(f"Duplicate Question_ID {question_id!r} on CSV row {row_number}")
        seen_ids.add(question_id)
        if question["Correct_Answer"] not in {"A", "B", "C", "D"}:
            raise ValueError(f"Invalid Correct_Answer for {question_id}")
    return questions


def filter_questions(
    questions: list[dict[str, str]],
    *,
    module: str | None = None,
    difficulty: str | None = None,
    skills: set[str] | None = None,
    question_ids: set[str] | None = None,
) -> list[dict[str, str]]:
    """Return questions matching the provided filters."""
    return [
        question for question in questions
        if (module is None or question["Module"] == module)
        and (difficulty is None or question["Difficulty"] == difficulty)
        and (skills is None or question["Skill"] in skills)
        and (question_ids is None or question["Question_ID"] in question_ids)
    ]
