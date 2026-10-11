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
    assert len(questions) == 70
    assert {question["Module"] for question in questions} == {"Math", "Reading & Writing"}


def test_original_pilot_content_integrity():
    from collections import Counter
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "SAT_question_bank_MVP.csv"
    pilot = [q for q in load_questions(path) if q["Question_ID"].startswith("P_")]
    assert len(pilot) == 20
    assert Counter(q["Module"] for q in pilot) == {"Math": 10, "Reading & Writing": 10}
    assert Counter(q["Correct_Answer"] for q in pilot) == dict.fromkeys("ABCD", 5)
    for module in {q["Module"] for q in pilot}:
        assert Counter(q["Difficulty"] for q in pilot if q["Module"] == module) == {
            "Easy": 3, "Medium": 4, "Hard": 3,
        }
    for question in pilot:
        choices = [question[f"Choice_{letter}"] for letter in "ABCD"]
        assert all(choices) and len(set(choices)) == 4
        assert question["Correct_Text"] == question[f"Choice_{question['Correct_Answer']}"]
        assert question["Explanation"]
        assert "not independently educator-reviewed" in question["Provenance"]
        assert int(question["Estimated_Time_Sec"]) > 0


def test_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "bank.csv"
    write_bank(path, [make_row(), make_row()])
    with pytest.raises(ValueError, match="Duplicate"):
        load_questions(path)


def test_filter_questions():
    questions = [make_row(), make_row("Q2", module="Reading & Writing", skill="Inference", difficulty="Medium")]
    assert [q["Question_ID"] for q in filter_questions(questions, module="Math", difficulty="Easy")] == ["Q1"]
