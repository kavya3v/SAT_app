"""Mistake review and practice recommendations."""

import streamlit as st

from sat_prep.services.practice import build_recommendations
from sat_prep.storage import repository


def render(db_path, questions: list[dict[str, str]]):
    st.title("Area of Improvement")
    history = repository.get_answer_history(db_path)
    if not history:
        st.info("Answer questions during a practice session to see your progress here.")
        return

    total = len(history)
    correct = sum(bool(answer["is_correct"]) for answer in history)
    cols = st.columns(3)
    cols[0].metric("Questions answered", total)
    cols[1].metric("Accuracy", f"{correct / total:.0%}")
    cols[2].metric("Needs review", sum(not bool(a["is_correct"]) for a in history))

    q_by_id = {q["Question_ID"]: q for q in questions}
    mistakes = repository.get_mistakes(db_path)
    st.subheader("Mistakes to review")
    if mistakes:
        for mistake in mistakes[:20]:
            question = q_by_id.get(str(mistake["question_id"]))
            if question:
                with st.expander(f"{question['Question_ID']} · {question['Skill']} · You chose {mistake['selected_answer']}"):
                    st.write(question["Question"])
                    st.write(f"**Correct answer:** {question['Correct_Answer']}. {question['Correct_Text']}")
                    st.write(question["Explanation"])
    else:
        st.success("No missed answers yet. Keep practicing!")

    st.subheader("What to practice next")
    recommendations = build_recommendations([
        {"skill": answer["skill"], "is_correct": answer["is_correct"]} for answer in history
    ])
    if recommendations:
        for item in recommendations:
            st.write(f"**{item['skill']}** — {item['accuracy']:.0%} accuracy across {item['attempts']} attempts")
    else:
        st.write("Answer at least two questions in a skill to get a targeted recommendation.")
