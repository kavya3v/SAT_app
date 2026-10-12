"""Streamlit entry point for the SAT Prep app."""

from pathlib import Path
import os

import streamlit as st

from sat_prep.pages import dashboard, home, practice, progress
from sat_prep.services.question_bank import load_questions
from sat_prep.services.vocabulary import daily_word
from sat_prep.storage.database import initialize
from sat_prep.storage.configuration import database_target

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "SAT_question_bank_MVP.csv"
DB_PATH = ROOT / "data" / "sat_prep.db"


@st.fragment(run_every="60s")
def _word_of_the_day():
    word = daily_word()
    with st.container(border=True):
        st.caption("SAT word of the day")
        st.markdown(f"**{word['word'].capitalize()}** — {word['meaning']}")


def main():
    st.set_page_config(page_title="SAT Prep", page_icon="📘", layout="wide")
    try:
        if 'SAT_DATABASE_URL' in os.environ:
            settings = {'SAT_DATABASE_URL': os.environ['SAT_DATABASE_URL']}
        else:
            try:
                settings = st.secrets
                # Access inside the guard: missing secrets files are loaded lazily.
                settings = {'SAT_DATABASE_URL': settings['SAT_DATABASE_URL']} if 'SAT_DATABASE_URL' in settings else {}
            except FileNotFoundError:
                settings = {}
        db_path = database_target(DB_PATH, settings)
        initialize(db_path)
    except Exception:
        st.error('Could not initialize progress storage. Check the database configuration and connection. Credentials are not displayed.')
        st.stop()
    try:
        questions = load_questions(CSV_PATH)
    except (OSError, ValueError) as error:
        st.error(f"Could not load the question bank: {error}")
        st.stop()

    with st.sidebar:
        st.title("SAT Prep")
        st.caption("A little progress, every day.")
        selected_page = st.radio("Navigate", ["Home", "Dashboard", "Practice", "Progress"], key="page")
        st.divider()
        st.caption(f"{len(questions)} questions · Math and Reading & Writing")
        st.caption("20-minute daily goal")

    _, word_column = st.columns([3, 2])
    with word_column:
        _word_of_the_day()

    if selected_page == "Home":
        home.render(db_path, questions)
    elif selected_page == "Dashboard":
        dashboard.render(db_path, questions)
    elif selected_page == "Practice":
        practice.render(db_path, questions)
    else:
        progress.render(db_path, questions)


if __name__ == "__main__":
    main()
