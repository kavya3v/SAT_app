from datetime import datetime, timezone

from sat_prep.storage import repository
from sat_prep.storage.database import initialize


def test_saves_profile_answers_and_completed_sessions(tmp_path):
    db = tmp_path / "test.db"
    initialize(db)
    repository.save_profile(db, "Asha")
    assert repository.get_profile(db)["name"] == "Asha"
    started = datetime(2026, 10, 5, tzinfo=timezone.utc)
    session_id = repository.start_session(db, started)
    question = {"Question_ID": "Q1", "Skill": "Algebra", "Module": "Math"}
    repository.save_answer(db, session_id, question, "A", False, started)
    repository.complete_session(db, session_id, started, 1200)
    assert repository.get_mistakes(db)[0]["question_id"] == "Q1"
    assert repository.completed_session_dates(db)[0].isoformat() == "2026-10-05"
