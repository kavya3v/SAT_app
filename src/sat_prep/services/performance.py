"""Practice summaries and comparisons with published historical SAT statistics."""

from collections import defaultdict

SAT_2025 = {"total": 1029, "rw": 521, "math": 508}
# College Board 2025 annual report, "Score Distributions", total-score bands.
SAT_2025_COUNTS = (
    ('400–590', 52_472), ('600–790', 281_174), ('800–990', 609_159),
    ('1000–1190', 554_819), ('1200–1390', 357_574), ('1400–1600', 149_767),
)
REPORT_URL = "https://reports.collegeboard.org/media/pdf/2025-total-group-sat-suite-of-assessments-annual-report.pdf"
BENCHMARK_URL = "https://satsuite.collegeboard.org/k12-educators/about/understand-scores-benchmarks/benchmarks"
SCORING_URL = "https://satsuite.collegeboard.org/scores/what-scores-mean/how-scores-calculated"
SCORE_RANGES = {"SAT": (200, 800), "Bluebook SAT practice": (200, 800),
                "PSAT/NMSQT or PSAT 10": (160, 760), "PSAT 8/9": (120, 720)}


def sat_2025_distribution():
    """Compute percentages from counts instead of the report's rounded percentages."""
    total = sum(count for _, count in SAT_2025_COUNTS)
    return [{'Score range': band, 'Students': count, 'Percent of students': count / total * 100}
            for band, count in SAT_2025_COUNTS]


def validate_scores(test_type, rw, math):
    if test_type not in SCORE_RANGES:
        raise ValueError("Choose a supported test type.")
    low, high = SCORE_RANGES[test_type]
    for value in (rw, math):
        if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high or value % 10:
            raise ValueError(f"Section scores must be multiples of 10 between {low} and {high}.")


def compare_sat(rw, math):
    validate_scores("SAT", rw, math)
    return dict(total=rw + math, total_delta=rw + math - SAT_2025["total"],
                rw_delta=rw - SAT_2025["rw"], math_delta=math - SAT_2025["math"],
                rw_benchmark_met=rw >= 480, math_benchmark_met=math >= 530)


def practice_summary(history):
    # Later submissions after feedback must not inflate first-attempt accuracy.
    first = {}
    for answer in sorted(history, key=lambda a: (a["answered_at"], a["id"])):
        first.setdefault((answer["session_id"], answer["question_id"]), answer)
    answers = list(first.values())
    subjects, skills, daily = defaultdict(list), defaultdict(list), defaultdict(list)
    for answer in answers:
        correct = bool(answer["is_correct"])
        subjects[answer["module"]].append(correct)
        skills[(answer["module"], answer["skill"])].append(correct)
        daily[answer["answered_at"][:10]].append(correct)
    def accuracy(values):
        return 100 * sum(values) / len(values)
    return {
        "attempts": len(answers), "unique_questions": len({a["question_id"] for a in answers}),
        "accuracy": sum(bool(a["is_correct"]) for a in answers) / len(answers) if answers else None,
        "subjects": [{"Subject": name, "Attempts": len(values), "Accuracy": accuracy(values)}
                     for name, values in sorted(subjects.items())],
        "skills": [{"Subject": module, "Skill": skill, "Attempts": len(values), "Accuracy": accuracy(values)}
                   for (module, skill), values in sorted(skills.items(), key=lambda item: accuracy(item[1]))],
        "daily": [{"Date": day, "Attempts": len(values), "Accuracy": accuracy(values)}
                  for day, values in sorted(daily.items())],
    }
