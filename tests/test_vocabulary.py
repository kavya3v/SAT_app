from datetime import date, timedelta

from sat_prep.services.vocabulary import daily_word


def test_daily_word_is_stable_and_changes_next_day():
    day = date(2028, 2, 28)
    assert daily_word(day) == daily_word(day)
    assert daily_word(day)['word'] != daily_word(day + timedelta(days=1))['word']
    assert daily_word(day + timedelta(days=1))['word'] != daily_word(day + timedelta(days=2))['word']
    assert daily_word(day)['meaning']
