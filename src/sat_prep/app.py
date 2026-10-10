"""Streamlit entry point for the SAT Prep app."""

from pathlib import Path

import streamlit as st

from sat_prep.pages import home, practice, progress
from sat_prep.services.question_bank import load_questions
from sat_prep.storage.database import initialize

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "SAT_question_bank_MVP.csv"
DB_PATH = ROOT / "data" / "sat_prep.db"


def main():
    st.set_page_config(page_title="SAT Prep", page_icon="📘", layout="wide")
    st.markdown("""
    <style>
      .stApp { background: #f7f8fc; }
      [data-testid="stMetric"] { background: white; padding: 1rem; border-radius: 14px; border: 1px solid #e7e9f2; }
      div.stButton > button[kind="primary"] { border-radius: 10px; min-height: 3rem; }
    </style>
    """, unsafe_allow_html=True)
    initialize(DB_PATH)
    try:
        questions = load_questions(CSV_PATH)
    except (OSError, ValueError) as error:
        st.error(f"Could not load the question bank: {error}")
        st.stop()

    with st.sidebar:
        st.title("SAT Prep")
        selected_page = st.radio("Navigate", ["Home", "Practice", "Progress"], key="page")
        st.divider()
        st.caption(f"{len(questions)} questions · Math and Reading & Writing")
        st.caption("20-minute daily goal")

    if selected_page == "Home":
        home.render(DB_PATH)
    elif selected_page == "Practice":
        practice.render(DB_PATH, questions)
    else:
        progress.render(DB_PATH, questions)


if __name__ == "__main__":
    main()
