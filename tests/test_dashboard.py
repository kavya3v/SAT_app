from datetime import date, datetime

import pytest
import altair  # Load chart dependencies before the timed AppTest script run.
import pandas
from streamlit import env_util
from streamlit.testing.v1 import AppTest

from sat_prep.storage import repository
from sat_prep.storage.database import initialize


@pytest.fixture(autouse=True)
def non_interactive_test_environment(monkeypatch):
    # Streamlit's REPL-warning check calls inspect.stack(), which scans source
    # paths very slowly in this Windows sandbox. These tests are never a REPL;
    # bypass that environment probe without mocking the UI or its calculations.
    monkeypatch.setattr(env_util, 'is_repl', lambda: False)


def dashboard_app(db):
    return AppTest.from_string(
        "from sat_prep.pages.dashboard import render\n"
        f"render({str(db)!r}, [{{'Question_ID': 'Q1'}}])\n",
        default_timeout=90,
    ).run()


def test_dashboard_empty_state_and_score_entry(tmp_path):
    db = tmp_path / 'empty.db'
    initialize(db)
    app = dashboard_app(db)
    assert not app.exception
    assert app.metric[1].value == 'No data'
    assert any(heading.value == '2025 SAT total-score distribution' for heading in app.subheader)
    for label, value in [('Reading & Writing score', 600), ('Math score', 650)]:
        next(widget for widget in app.number_input if widget.label == label).set_value(value)
    next(button for button in app.button if button.label == 'Save test result').click().run()
    assert not app.exception
    assert repository.get_scores(db)[0]['math'] == 650
    assert any(metric.label == 'Reported total' and metric.value == '1250' for metric in app.metric)
    next(button for button in app.button if button.label == 'Delete selected result').click().run()
    assert not app.exception
    assert repository.get_scores(db) == []


def test_dashboard_practice_charts_and_psat_separation(tmp_path):
    db = tmp_path / 'history.db'
    initialize(db)
    started = datetime(2026, 1, 1, 10)
    session = repository.start_session(db, started)
    question = {'Question_ID': 'Q1', 'Module': 'Math', 'Skill': 'Algebra'}
    repository.save_answer(db, session, question, 'A', False, started)
    repository.save_score(db, 'PSAT 8/9', date(2026, 1, 1), 500, 520)
    app = dashboard_app(db)
    assert not app.exception
    assert app.metric[1].value == '0%'
    assert not any(metric.label == 'Reported total' for metric in app.metric)
    assert any('PSAT results are logged separately' in info.value for info in app.info)


def test_daily_word_remains_visible_when_navigating_all_pages(tmp_path):
    from pathlib import Path

    bank = Path(__file__).resolve().parents[1] / 'SAT_question_bank_MVP.csv'
    db = tmp_path / 'navigation.db'
    app = AppTest.from_string(
        "from pathlib import Path\n"
        "from sat_prep import app\n"
        f"app.DB_PATH = Path({str(db)!r})\n"
        f"app.CSV_PATH = Path({str(bank)!r})\n"
        "app.main()\n", default_timeout=90,
    ).run()
    assert not app.exception
    first_word = next(item.value for item in app.markdown if '**' in item.value and '—' in item.value)
    for page in ('Dashboard', 'Practice', 'Progress', 'Home'):
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception
        assert any(caption.value == 'SAT word of the day' for caption in app.caption)
        assert any(item.value == first_word for item in app.markdown)
