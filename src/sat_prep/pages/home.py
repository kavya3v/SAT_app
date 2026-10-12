"""Student profile and personalized dashboard."""

from datetime import date
from html import escape

import streamlit as st

from sat_prep.services.streaks import calculate_streak, completed_today
from sat_prep.storage import repository


def _start_practice(subject=None):
    """Navigate before the sidebar radio is recreated on the next rerun."""
    st.session_state["page"] = "Practice"
    st.session_state["start_session"] = True
    st.session_state["practice_subject"] = subject or "All subjects"


def _navigate(page):
    st.session_state["page"] = page


def _welcome(name, graduation_year):
    # Only these locally owned classes are styled. Student input is escaped.
    return f"""
    <style>
      .sat-welcome {{ display:flex; align-items:center; justify-content:space-between;
        gap:1.25rem; padding:1.25rem 1.75rem; border-radius:20px; background:#142D4E;
        color:#F8F7F3; overflow:hidden; margin:0 0 .75rem; }}
      .sat-welcome-copy {{ max-width:760px; min-width:0; }}
      .sat-eyebrow {{ color:#BDE9E7; font-size:.8rem; font-weight:700;
        letter-spacing:.08em; text-transform:uppercase; margin:0 0 .45rem; }}
      .sat-welcome h1 {{ color:#FFFFFF; font-size:clamp(1.4rem,2.2vw,2rem);
        letter-spacing:-.025em; line-height:1.2; margin:0 0 .5rem; padding:0; }}
      .sat-welcome-description {{ color:#E4EBEE; font-size:.95rem; line-height:1.5;
        margin:0 0 .65rem; }}
      .sat-goal-tag {{ display:inline-block; border:1px solid #F2C66D; border-radius:999px;
        padding:.35rem .8rem; color:#142D4E; background:#F2C66D; font-size:.8rem; }}
      .sat-welcome-art {{ width:130px; min-width:100px; flex-shrink:0; }}
      @media(max-width:700px) {{ .sat-welcome {{ padding:1.1rem; }}
        .sat-welcome-art {{ display:none; }} }}
    </style>
    <section class="sat-welcome" aria-label="Your SAT learning journey">
      <div class="sat-welcome-copy">
        <p class="sat-eyebrow">Your learning journey · Welcome, {escape(str(name))}</p>
        <h1>Small steps. Big possibilities.</h1>
        <p class="sat-welcome-description">Build confidence with one focused practice session today.</p>
        <span class="sat-goal-tag">Class of {int(graduation_year)} · One day at a time</span>
      </div>
      <svg class="sat-welcome-art" viewBox="0 0 280 240" aria-hidden="true" focusable="false">
        <circle cx="140" cy="120" r="102" fill="#244666"/>
        <circle cx="140" cy="120" r="80" fill="none" stroke="#6C879B" stroke-dasharray="5 8"/>
        <path d="M56 100 Q97 83 140 104 Q183 83 224 100 L224 177 Q183 160 140 181 Q97 160 56 177Z" fill="#BDE9E7"/>
        <path d="M62 92 Q102 79 140 98 L140 170 Q102 151 62 164Z" fill="#FFFFFF"/>
        <path d="M140 98 Q179 79 218 92 L218 164 Q179 151 140 170Z" fill="#F8F7F3"/>
        <path d="M140 99 L140 175" stroke="#087E8B" stroke-width="3"/>
        <path d="M77 110 L122 113 M77 123 L122 126 M77 136 L111 139" stroke="#6C879B" stroke-width="4" stroke-linecap="round"/>
        <text x="158" y="135" fill="#142D4E" font-size="26" font-family="sans-serif" font-weight="700">x + y</text>
        <path d="M166 53 L220 29 L200 80 L190 58Z" fill="#F2C66D"/>
        <path d="M190 58 L220 29" stroke="#087E8B" stroke-width="2"/>
        <path d="M60 55 L60 69 M53 62 L67 62 M225 193 L225 205 M219 199 L231 199" stroke="#BDE9E7" stroke-width="3" stroke-linecap="round"/>
        <circle cx="40" cy="142" r="4" fill="#F2C66D"/><circle cx="235" cy="95" r="4" fill="#BDE9E7"/>
      </svg>
    </section>
    """


def render(db_path, questions=None):
    profile = repository.get_profile(db_path)
    plan = repository.get_preparation_plan(db_path)
    st.html(_welcome(profile['name'], plan['graduation_year']))

    today = date.today()
    days = repository.completed_session_dates(db_path)
    streak = calculate_streak(days, today)
    did_today = completed_today(days, today)
    mission, momentum = st.columns([1.7, 1], gap="large")
    with mission, st.container(border=True):
        st.subheader("Your 20-minute mission", anchor=False)
        st.write("Pick a subject, take your time, and learn something new. You don't have to get every answer right to make progress.")
        st.button("Start today's practice", type="primary", icon=":material/play_arrow:",
                  width="stretch", on_click=_start_practice)
        st.caption("Choose Math, Reading & Writing, or a mix in practice settings.")
    with momentum, st.container(border=True):
        st.subheader("Keep your momentum", anchor=False)
        st.metric("Practice streak", f"{streak} {'day' if streak == 1 else 'days'}")
        st.progress(1.0 if did_today else 0.0,
                    text="Today's goal is complete. Nice work!" if did_today else "Today's goal: one 20-minute session")
        st.caption("Start a new streak today." if streak == 0 else "Every focused session is another step forward.")

    st.subheader("Your learning path", anchor=False)
    st.caption("Two subjects. Lots of ways to grow. Choose where you'd like to begin.")
    math_card, reading_card = st.columns(2, gap="large")
    for column, subject, icon, heading, description, button in (
        (math_card, 'Math', 'calculate', 'Build your math confidence',
         'Explore algebra, functions, data, geometry, and problem-solving. Work through one idea at a time.', 'Practice math'),
        (reading_card, 'Reading & Writing', 'menu_book', 'Find your voice. Sharpen your thinking.',
         'Practice understanding passages, weighing evidence, and choosing clear, effective language.', 'Practice reading & writing'),
    ):
        with column, st.container(border=True):
            st.markdown(f":material/{icon}: **{subject.upper()}**")
            st.markdown(f"### {heading}")
            st.write(description)
            if questions is not None:
                count = sum(q['Module'] == subject for q in questions)
                st.caption(f"{count} practice questions · Easy, Medium & Hard")
            st.button(button, icon=":material/arrow_forward:", width="stretch",
                      on_click=_start_practice, args=(subject,))

    st.subheader("Make your next step count", anchor=False)
    progress_card, review_card = st.columns(2, gap="large")
    with progress_card, st.container(border=True):
        st.markdown("**See how you're growing**")
        st.write("Explore your practice trends, log a test score, and track your goals.")
        st.button("View my dashboard", icon=":material/bar_chart:",
                  on_click=_navigate, args=('Dashboard',))
    with review_card, st.container(border=True):
        st.markdown("**Turn mistakes into discoveries**")
        st.write("Revisit explanations and find the skills to practice next.")
        st.button("Review my progress", icon=":material/lightbulb:",
                  on_click=_navigate, args=('Progress',))

    with st.expander("Make it yours", icon=":material/person:"):
        with st.form("profile_form"):
            name = st.text_input("Student name", value=str(profile["name"]))
            if st.form_submit_button("Save profile"):
                repository.save_profile(db_path, name)
                st.rerun()
