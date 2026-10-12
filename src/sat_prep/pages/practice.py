"""Interactive SAT practice workspace."""

from datetime import datetime
import random
import time

import streamlit as st

from sat_prep.services.practice import can_complete_session, is_correct
from sat_prep.services.question_bank import filter_questions
from sat_prep.storage import repository


@st.fragment(run_every="1s")
def _session_timer(started_at):
    elapsed = int(time.time() - started_at)
    remaining = max(0, 20 * 60 - elapsed)
    st.progress(min(1.0, elapsed / (20 * 60)), text=f"{remaining // 60:02}:{remaining % 60:02} remaining")
    if elapsed >= 20 * 60 and not st.session_state.get("session_goal_reached"):
        st.session_state["session_goal_reached"] = True
        st.rerun(scope="app")


def _start(db_path):
    now = datetime.now().astimezone()
    st.session_state["session_id"] = repository.start_session(db_path, now)
    st.session_state["session_started"] = time.time()
    st.session_state["session_goal_reached"] = False
    st.session_state["question_index"] = 0
    st.session_state["answered"] = False
    st.session_state["question_order"] = []


def _clear_session_state():
    for key in ("session_id", "session_started", "session_goal_reached", "question_order", "question_index", "answered"):
        st.session_state.pop(key, None)


def _finish_session(db_path):
    session_id = st.session_state.get("session_id")
    started = st.session_state.get("session_started")
    if session_id is not None and started is not None:
        elapsed = int(time.time() - started)
        repository.complete_session(db_path, session_id, datetime.now().astimezone(), elapsed)
    _clear_session_state()
    st.session_state["page"] = "Home"


def _abandon_session(db_path):
    session_id = st.session_state.get("session_id")
    started = st.session_state.get("session_started")
    if session_id is not None and started is not None:
        elapsed = int(time.time() - started)
        repository.abandon_session(db_path, session_id, datetime.now().astimezone(), elapsed)
    _clear_session_state()
    st.session_state["page"] = "Home"


def render(db_path, questions: list[dict[str, str]]):
    st.title("Smart Practice")
    if st.session_state.pop("start_session", False):
        _start(db_path)
    if "session_id" not in st.session_state:
        st.info("Start a 20-minute session from Home when you're ready.")
        return

    elapsed = int(time.time() - st.session_state["session_started"])
    _session_timer(st.session_state["session_started"])
    with st.expander("Practice settings", expanded=False):
        modules = ["All subjects"] + sorted({q["Module"] for q in questions})
        module = st.selectbox("Subject", modules, key="practice_subject")
        levels = sorted({q["Difficulty"] for q in questions})
        difficulty = st.selectbox("Difficulty", ["All levels", *levels])
        if st.button("Apply filters"):
            st.session_state["question_order"] = []
            st.session_state["question_index"] = 0
            st.session_state["answered"] = False

    module_filter = None if module == "All subjects" else module
    difficulty_filter = None if difficulty == "All levels" else difficulty
    available = filter_questions(questions, module=module_filter, difficulty=difficulty_filter)
    if not available:
        st.warning("No questions match these settings.")
        return
    if not st.session_state.get("question_order"):
        order = [q["Question_ID"] for q in available]
        random.shuffle(order)
        st.session_state["question_order"] = order
    by_id = {q["Question_ID"]: q for q in available}
    order = [qid for qid in st.session_state["question_order"] if qid in by_id]
    if not order:
        st.session_state["question_order"] = []
        st.rerun()
    index = st.session_state["question_index"] % len(order)
    question = by_id[order[index]]
    st.caption(f"{question['Module']} · {question['Domain']} · {question['Skill']} · {question['Difficulty']}")
    st.subheader(question["Question"])

    choices = {letter: question[f"Choice_{letter}"] for letter in "ABCD"}
    with st.form(f"answer_{question['Question_ID']}_{index}"):
        selected = st.radio("Choose your answer", list(choices), format_func=lambda key: f"{key}. {choices[key]}", index=None)
        submitted = st.form_submit_button("Check answer", type="primary")
    if submitted and selected:
        correct = is_correct(question, selected)
        repository.save_answer(db_path, st.session_state["session_id"], question, selected, correct, datetime.now().astimezone())
        st.session_state["answered"] = True
        st.session_state["last_correct"] = correct
    if st.session_state.get("answered"):
        if st.session_state.get("last_correct"):
            st.success("Correct!")
        else:
            st.error(f"Not quite. The correct answer is {question['Correct_Answer']}: {question['Correct_Text']}")
        if st.button("Show hint", key=f"hint_{index}"):
            st.info(f"Hint: Focus on the skill **{question['Skill']}** and identify what the question asks you to find.")
        with st.expander("Step-by-step explanation"):
            st.write(question["Explanation"])
        if st.button("Next question"):
            st.session_state["question_index"] += 1
            st.session_state["answered"] = False
            st.rerun()

    if can_complete_session(elapsed):
        st.success("20 minutes complete. You can finish and record today's practice streak.")
        st.button(
            "Finish session", type="primary",
            on_click=_finish_session, args=(db_path,),
        )
    else:
        st.button(
            "End session without completing goal",
            on_click=_abandon_session, args=(db_path,),
        )
