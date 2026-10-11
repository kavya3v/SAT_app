from datetime import date

import pytest

from sat_prep.services.performance import compare_sat, practice_summary, sat_2025_distribution
from sat_prep.storage import repository
from sat_prep.storage.database import initialize


def test_2025_distribution_accounts_for_entire_reported_cohort():
    distribution = sat_2025_distribution()
    assert sum(row['Students'] for row in distribution) == 2_004_965
    assert sum(row['Percent of students'] for row in distribution) == pytest.approx(100)
    assert distribution[0]['Score range'] == '400–590'
    assert distribution[-1]['Score range'] == '1400–1600'
    assert distribution[-1]['Students'] == 149_767


def test_practice_summary_uses_first_attempt_per_session_question():
    history = [
        dict(id=3, session_id=1, question_id='Q1', module='Math', skill='Algebra',
             is_correct=1, answered_at='2026-10-11T10:02:00'),
        dict(id=2, session_id=1, question_id='Q2', module='Math', skill='Algebra',
             is_correct=1, answered_at='2026-10-11T10:01:00'),
        dict(id=1, session_id=1, question_id='Q1', module='Math', skill='Algebra',
             is_correct=0, answered_at='2026-10-11T10:00:00'),
    ]
    summary = practice_summary(history)
    assert summary['attempts'] == 2
    assert summary['accuracy'] == 0.5
    assert summary['subjects'][0]['Accuracy'] == 50
    assert summary['daily'][0]['Accuracy'] == 50
    assert practice_summary([])['accuracy'] is None


def test_sat_comparison_requires_valid_section_scores():
    result = compare_sat(600, 650)
    assert result['total'] == 1250
    assert result['total_delta'] == 221
    assert result['rw_delta'] == 79
    assert result['math_delta'] == 142
    assert result['rw_benchmark_met'] and result['math_benchmark_met']
    assert not compare_sat(470, 520)['rw_benchmark_met']
    for rw, math in [(190, 600), (600, 810), (605, 600)]:
        with pytest.raises(ValueError):
            compare_sat(rw, math)


def test_score_log_and_plan_survive_reinitialization(tmp_path):
    db = tmp_path / 'scores.db'
    initialize(db)
    repository.save_preparation_plan(db, 2030, 1400)
    repository.save_score(db, 'SAT', date(2026, 10, 1), 600, 650)
    repository.save_score(db, 'PSAT 8/9', date(2026, 9, 1), 500, 520)
    initialize(db)
    assert repository.get_preparation_plan(db) == {'graduation_year': 2030, 'target_score': 1400}
    scores = repository.get_scores(db)
    assert scores[0]['test_type'] == 'SAT'
    assert len(scores) == 2
    with pytest.raises(ValueError):
        repository.save_score(db, 'PSAT 8/9', date(2026, 10, 1), 800, 800)
    with pytest.raises(ValueError):
        repository.save_score(db, 'SAT', date(2026, 10, 1), 605, 600)
    assert len(repository.get_scores(db)) == 2
