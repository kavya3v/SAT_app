"""Family preparation dashboard: practice activity and self-reported test scores."""

from datetime import date

import pandas as pd
import altair as alt
import streamlit as st

from sat_prep.services.performance import (
    BENCHMARK_URL, REPORT_URL, SAT_2025, SCORE_RANGES, SCORING_URL,
    compare_sat, practice_summary, sat_2025_distribution,
)
from sat_prep.storage import repository


def render(db_path, questions):
    plan = repository.get_preparation_plan(db_path)
    st.title("SAT performance dashboard")
    st.caption(f"Preparing for high school graduation in {plan['graduation_year']} · Target SAT score: {plan['target_score']}")
    st.caption("Graduation year is a planning goal. The 2025 results are a historical comparison, not a prediction for 2030.")

    with st.expander("Preparation goals"):
        with st.form("preparation_goals"):
            graduation = st.number_input("High school graduation year", min_value=2026, max_value=2050,
                                         value=plan['graduation_year'], step=1)
            target = st.number_input("Target SAT total", min_value=400, max_value=1600,
                                     value=plan['target_score'], step=10)
            st.caption("1400 is an editable starting goal, not an admissions requirement.")
            if st.form_submit_button("Save goals"):
                repository.save_preparation_plan(db_path, int(graduation), int(target))
                st.rerun()

    practice_tab, score_tab = st.tabs(["Practice performance", "Test scores and 2025 comparison"])
    with practice_tab:
        summary = practice_summary(repository.get_answer_history(db_path))
        st.caption("Accuracy counts the first answer for each question in each session. Repeated questions in later sessions count again.")
        cols = st.columns(3)
        cols[0].metric("First attempts", summary['attempts'])
        cols[1].metric("Practice accuracy", f"{summary['accuracy']:.0%}" if summary['accuracy'] is not None else "No data")
        cols[2].metric("Bank coverage", f"{summary['unique_questions']} / {len(questions)}")
        st.info("Practice accuracy is not a SAT score. These original questions have not been calibrated to the SAT scoring scale.")
        if summary['attempts']:
            st.subheader("Performance by subject")
            frame = pd.DataFrame(summary['subjects'])
            st.bar_chart(frame, x="Subject", y="Accuracy", y_label="Accuracy (%)", alt="Practice accuracy by subject")
            st.dataframe(frame, hide_index=True, alt="Subject accuracy and attempt counts")
            st.subheader("Daily practice accuracy")
            daily = pd.DataFrame(summary['daily'])
            daily['Date'] = pd.to_datetime(daily['Date'])
            st.line_chart(daily, x="Date", y="Accuracy", y_label="Accuracy (%)", alt="Daily first-attempt practice accuracy")
            st.dataframe(daily, hide_index=True, alt="Daily practice accuracy and attempt counts")
            st.subheader("Skills to strengthen")
            st.dataframe(summary['skills'], hide_index=True, alt="Skills ordered by accuracy with attempt counts")
            st.caption("Small samples can be misleading. Use attempt counts and fresh questions when assessing improvement.")
        else:
            st.info("Start a practice session and answer questions to populate this dashboard.")

    with score_tab:
        st.subheader("Add a test result")
        # Outside the form so score bounds update as soon as the test type changes.
        test_type = st.selectbox("Test type", list(SCORE_RANGES))
        low, high = SCORE_RANGES[test_type]
        with st.form(f"score_entry_{test_type}", clear_on_submit=True):
            test_date = st.date_input("Test date", value=date.today(), max_value=date.today())
            rw = st.number_input("Reading & Writing score", min_value=low, max_value=high, value=low, step=10)
            math = st.number_input("Math score", min_value=low, max_value=high, value=low, step=10)
            st.caption("Enter section scores from your score report. No score is assumed until you save.")
            if st.form_submit_button("Save test result"):
                try:
                    repository.save_score(db_path, test_type, test_date, int(rw), int(math))
                except ValueError as error:
                    st.error(str(error))
                else:
                    st.rerun()

        scores = repository.get_scores(db_path)
        sat_scores = [score for score in scores if score['test_type'] in ('SAT', 'Bluebook SAT practice')]
        st.subheader("2025 historical reference")
        st.table([{"Measure": "Total", "2025 average": SAT_2025['total']},
                  {"Measure": "Reading & Writing", "2025 average": SAT_2025['rw']},
                  {"Measure": "Math", "2025 average": SAT_2025['math']}], alt="2025 graduating class SAT averages")
        st.caption("Population: students graduating high school in 2025 who took the SAT; most recent score per student. This is not the average for one 2025 test date.")
        st.markdown(f"Source: [College Board 2025 annual report]({REPORT_URL}) · Checked October 11, 2026.")
        st.subheader("2025 SAT total-score distribution")
        distribution = pd.DataFrame(sat_2025_distribution())
        chart = alt.Chart(distribution).mark_bar(color='#087E8B').encode(
            x=alt.X('Score range:N', sort=distribution['Score range'].tolist(), title='SAT total score'),
            y=alt.Y('Percent of students:Q', title='Students (%)', scale=alt.Scale(domain=[0, 35])),
            tooltip=[alt.Tooltip('Score range:N'), alt.Tooltip('Students:Q', format=','),
                     alt.Tooltip('Percent of students:Q', format='.1f')],
        )
        st.altair_chart(chart, alt="2025 graduating class SAT total scores, grouped from 400 to 1600; 800–990 is the largest group")
        st.caption("2,004,965 SAT takers in the graduating class of 2025. Percentages are calculated from the published counts; hover over a bar for details.")
        if sat_scores:
            labels = {s['id']: f"{s['test_date']} · {s['test_type']} · {s['reading_writing'] + s['math']}" for s in sat_scores}
            selected = st.selectbox("Result to analyze", list(labels), format_func=labels.get)
            score = next(s for s in sat_scores if s['id'] == selected)
            comparison = compare_sat(score['reading_writing'], score['math'])
            cols = st.columns(3)
            cols[0].metric("Reported total", comparison['total'], f"{comparison['total_delta']:+d} vs 2025 average")
            cols[1].metric("Reading & Writing", score['reading_writing'], f"{comparison['rw_delta']:+d} vs 2025 average")
            cols[2].metric("Math", score['math'], f"{comparison['math_delta']:+d} vs 2025 average")
            remaining = max(0, plan['target_score'] - comparison['total'])
            st.write(f"Points to your {plan['target_score']} target: **{remaining}**")
            st.write(f"Reading & Writing readiness benchmark (480): **{'Met' if comparison['rw_benchmark_met'] else 'Not yet met'}**")
            st.write(f"Math readiness benchmark (530): **{'Met' if comparison['math_benchmark_met'] else 'Not yet met'}**")
            st.caption("A Bluebook practice score is a practice result. Comparison with graduating SAT takers provides context, not an official percentile or admission prediction.")
            st.markdown(f"[College Board readiness benchmarks]({BENCHMARK_URL}) · [How SAT scoring works]({SCORING_URL})")
        else:
            st.info("Add a SAT or Bluebook SAT practice result to compare scores. PSAT results are logged separately and are not treated as SAT results.")
        if scores:
            st.subheader("Saved score history")
            st.dataframe([{"Date": s['test_date'], "Test": s['test_type'],
                           "Reading & Writing": s['reading_writing'], "Math": s['math'],
                           "Total": s['reading_writing'] + s['math']} for s in scores],
                         hide_index=True, alt="Saved self-reported test scores")
            for kind in ('SAT', 'Bluebook SAT practice'):
                trend = [s for s in reversed(scores) if s['test_type'] == kind]
                if len(trend) > 1:
                    st.subheader(f"{kind} score trend")
                    frame = pd.DataFrame([{"Date": pd.Timestamp(s['test_date']),
                                           "Total": s['reading_writing'] + s['math']} for s in trend])
                    st.line_chart(frame, x="Date", y="Total", alt=f"{kind} total scores over time")
            with st.expander("Remove an incorrectly entered result"):
                labels = {s['id']: f"{s['test_date']} · {s['test_type']} · {s['reading_writing'] + s['math']}" for s in scores}
                remove = st.selectbox("Saved result", list(labels), format_func=labels.get)
                if st.button("Delete selected result"):
                    repository.delete_score(db_path, remove)
                    st.rerun()
