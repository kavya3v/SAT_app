"""Practice-session rules and answer handling."""

SESSION_GOAL_SECONDS = 20 * 60


def is_correct(question: dict[str, str], selected_answer: str) -> bool:
    return selected_answer == question["Correct_Answer"]


def can_complete_session(elapsed_seconds: int | float) -> bool:
    return elapsed_seconds >= SESSION_GOAL_SECONDS


def build_recommendations(
    answers: list[dict[str, object]], *, min_attempts: int = 2
) -> list[dict[str, object]]:
    """Rank skills by low accuracy, then include unseen skills as exploration."""
    by_skill: dict[str, list[bool]] = {}
    for answer in answers:
        skill = str(answer["skill"])
        by_skill.setdefault(skill, []).append(bool(answer["is_correct"]))

    ranked = [
        {"skill": skill, "attempts": len(results), "accuracy": sum(results) / len(results)}
        for skill, results in by_skill.items()
        if len(results) >= min_attempts
    ]
    ranked.sort(key=lambda item: (item["accuracy"], -int(item["attempts"]), str(item["skill"])))
    return ranked[:3]
