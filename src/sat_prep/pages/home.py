"""Student profile and personalized dashboard."""

from datetime import date

import streamlit as st

from sat_prep.services.streaks import calculate_streak, completed_today
from sat_prep.storage import repository


def _start_practice():
    """Navigate before the sidebar radio is recreated on the next rerun."""
    st.session_state["page"] = "Practice"
    st.session_state["start_session"] = True


def render(db_path):
    profile = repository.get_profile(db_path)
    st.title(f"Welcome back, {profile['name']} 👋")
    st.caption("Build a steady SAT practice habit, one focused session at a time.")

    with st.form("profile_form"):
        name = st.text_input("Student name", value=str(profile["name"]))
        if st.form_submit_button("Save profile"):
            repository.save_profile(db_path, name)
            st.rerun()

    today = date.today()
    days = repository.completed_session_dates(db_path)
    streak = calculate_streak(days, today)
    did_today = completed_today(days, today)
    cols = st.columns(3)
    cols[0].metric("Current streak", f"{streak} days")
    cols[1].metric("Daily goal", "20 min")
    cols[2].metric("Today", "Complete ✓" if did_today else "Not started")

    st.subheader("Your next session")
    st.write("A focused 20-minute session keeps your streak going and helps us find your next practice target.")
    st.button(
        "Start Practice", type="primary", use_container_width=True,
        on_click=_start_practice,
    )
