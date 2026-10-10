import csv

import pytest

from sat_prep.services.question_bank import filter_questions, load_questions


def write_bank(path, rows):
    fields = ["Question_ID", "Module", "Domain", "Skill", "Difficulty", "Question", "Choice_A", "Choice_B", "Choice_C", "Choice_D", "Correct_Answer", "Correct_Text", "Explanation"]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def make_row(question_id="Q1", answer="A", module="Math", skill="Algebra", difficulty="Easy"):
    return {"Question_ID": question_id, "Module": module, "Domain": "Algebra", "Skill": skill, "Difficulty": difficulty, "Question": "Question?", "Choice_A": "one", "Choice_B": "two", "Choice_C": "three", "Choice_D": "four", "Correct_Answer": answer, "Correct_Text": "one", "Explanation": "Because."}


def test_loads_supplied_csv():
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "SAT_question_bank_MVP.csv"
    questions = load_questions(path)
    assert len(questions) == 50
    assert {question["Module"] for question in questions} == {"Math", "Reading & Writing"}


def test_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "bank.csv"
    write_bank(path, [make_row(), make_row()])
    with pytest.raises(ValueError, match="Duplicate"):
        load_questions(path)


def test_filter_questions():
    questions = [make_row(), make_row("Q2", module="Reading & Writing", skill="Inference", difficulty="Medium")]
    assert [q["Question_ID"] for q in filter_questions(questions, module="Math", difficulty="Easy")] == ["Q1"]
