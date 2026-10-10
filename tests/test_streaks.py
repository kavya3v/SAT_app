from datetime import date, timedelta

from sat_prep.services.streaks import calculate_streak, completed_today


def test_streak_counts_consecutive_days_ending_today():
    today = date(2026, 10, 5)
    assert calculate_streak([today, today - timedelta(days=1), today - timedelta(days=2)], today) == 3


def test_streak_remains_active_if_yesterday_was_last_session():
    today = date(2026, 10, 5)
    assert calculate_streak([today - timedelta(days=1), today - timedelta(days=2)], today) == 2


def test_streak_breaks_after_a_missed_day():
    today = date(2026, 10, 5)
    assert calculate_streak([today, today - timedelta(days=2)], today) == 1
    assert not completed_today([today - timedelta(days=1)], today)
