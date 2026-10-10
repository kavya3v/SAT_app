from sat_prep.services.practice import SESSION_GOAL_SECONDS, build_recommendations, can_complete_session, is_correct


def test_answer_is_checked_against_key():
    assert is_correct({"Correct_Answer": "B"}, "B")
    assert not is_correct({"Correct_Answer": "B"}, "A")


def test_session_requires_full_twenty_minutes():
    assert SESSION_GOAL_SECONDS == 1200
    assert not can_complete_session(1199)
    assert can_complete_session(1200)


def test_recommendations_rank_low_accuracy_skills():
    answers = [
        {"skill": "Algebra", "is_correct": False}, {"skill": "Algebra", "is_correct": True},
        {"skill": "Inference", "is_correct": False}, {"skill": "Inference", "is_correct": False},
    ]
    assert build_recommendations(answers)[0]["skill"] == "Inference"


def test_recommendations_skip_skills_with_too_few_answers():
    assert build_recommendations([{"skill": "Geometry", "is_correct": False}]) == []
