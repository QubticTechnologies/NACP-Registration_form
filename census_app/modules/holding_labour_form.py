import streamlit as st
from sqlalchemy import text
from census_app.db import engine

# ---------------- Holder Labour Form ----------------
def holding_labour_form(holder_id, prefix=""):
    """
    Render the Holding Labour form for a given holder.
    Automatically handles permanent/temporary workers and special questions.
    The `prefix` ensures unique Streamlit keys for multiple holders or survey sessions.
    """
    st.header("Section 2: Holding Labour")

    # Define questions for the holding labour form
    questions = [
        {"question_no": 2, "text": "How many permanent workers including administrative staff were hired on the holding from Aug 1, 2024 to Jul 31, 2025 (excluding household)?", "type": "count"},
        {"question_no": 3, "text": "How many temporary workers including administrative staff were hired on the holding from Aug 1, 2024 to Jul 31, 2025 (excluding household)?", "type": "count"},
        {"question_no": 4, "text": "What was the number of non-Bahamian workers on the holding from Aug 1, 2024 to Jul 31, 2025?", "type": "count"},
        {"question_no": 5, "text": "Did any of your workers have work permits?", "type": "option", "options": ["Yes", "No", "Not Applicable"]},
        {"question_no": 6, "text": "Were there any volunteer workers on the holding (i.e. unpaid labourers)?", "type": "option", "options": ["Yes", "No", "Not Applicable"]},
        {"question_no": 7, "text": "Did you use any agricultural contracted services (crop protection, pruning, composting, harvesting, animal services, irrigation, farm admin etc.) on the holding?", "type": "option", "options": ["Yes", "No", "Not Applicable"]},
    ]

    # Container for saving user responses
    responses = {}

    # Render each question
    for q in questions:
        q_no = q["question_no"]
        key_prefix = f"{prefix}_holder_{holder_id}_q{q_no}"

        if q["type"] == "count":
            # Render number inputs for male/female counts
            male = st.number_input(f"Male - {q['text']}", min_value=0, value=0, key=f"{key_prefix}_male")
            female = st.number_input(f"Female - {q['text']}", min_value=0, value=0, key=f"{key_prefix}_female")
            total = male + female
            st.write(f"Total: {total}")
            responses[q_no] = {"male": male, "female": female, "total": total, "option_response": None}

        elif q["type"] == "option":
            # Render selectbox for options
            option_response = st.selectbox(q["text"], options=q["options"], key=f"{key_prefix}_option")
            responses[q_no] = {"male": None, "female": None, "total": None, "option_response": option_response}

    # ---------------- Save Responses to Database ----------------
    if st.button("Save Section 2 Responses", key=f"{prefix}_save_button"):
        try:
            with engine.begin() as conn:
                for q_no, r in responses.items():
                    conn.execute(
                        text("""
                            INSERT INTO holding_labour (
                                holder_id, question_no, question_text, male_count, female_count, total_count, option_response
                            ) VALUES (
                                :holder_id, :q_no, :question_text, :male, :female, :total, :option_response
                            )
                            ON CONFLICT (holder_id, question_no) DO UPDATE
                            SET male_count = EXCLUDED.male_count,
                                female_count = EXCLUDED.female_count,
                                total_count = EXCLUDED.total_count,
                                option_response = EXCLUDED.option_response
                        """),
                        {
                            "holder_id": holder_id,
                            "q_no": q_no,
                            "question_text": q["text"],
                            "male": r["male"],
                            "female": r["female"],
                            "total": r["total"],
                            "option_response": r["option_response"]
                        }
                    )
            st.success("Section 2 responses saved successfully!")
        except Exception as e:
            st.error(f"Error saving responses: {e}")
