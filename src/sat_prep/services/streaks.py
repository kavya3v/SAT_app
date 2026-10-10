"""Daily practice streak calculations."""

from datetime import date, timedelta


def calculate_streak(completed_dates: list[date], today: date) -> int:
    """Count consecutive completed days ending today, or yesterday if today is open."""
    days = set(completed_dates)
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def completed_today(completed_dates: list[date], today: date) -> bool:
    return today in set(completed_dates)
