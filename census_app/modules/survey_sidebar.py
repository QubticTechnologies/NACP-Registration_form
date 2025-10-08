import streamlit as st
from sqlalchemy import text
from census_app.db import engine

# --------------------------
# Helper to safely save data
# --------------------------
def save_response(holder_id, section, data):
    """Insert or update survey responses with stability."""
    try:
        with engine.begin() as conn:
            for key, val in data.items():
                conn.execute(
                    text("""
                        INSERT INTO survey_responses (holder_id, section, question_key, response_value)
                        VALUES (:hid, :section, :key, :val)
                        ON CONFLICT (holder_id, section, question_key)
                        DO UPDATE SET response_value = EXCLUDED.response_value
                    """),
                    {"hid": holder_id, "section": section, "key": key, "val": val}
                )
        st.session_state[f"{section}_saved"] = True
        st.success(f"{section} saved successfully!")
    except Exception as e:
        st.error(f"Error saving {section}: {e}")


# --------------------------
# Section 1: Holder Info
# --------------------------
def holder_information_form(holder_id):
    st.subheader("Section 1: Holder Information")

    with st.form(key=f"holder_info_form_{holder_id}", clear_on_submit=False):
        name = st.text_input("Full Name of Holder")
        birth_date = st.date_input("Date of Birth", value=None, min_value=None, max_value=None)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        education = st.selectbox("Highest Level of Education", ["None", "Primary", "Secondary", "Tertiary"])
        years_farming = st.number_input("Years engaged in farming", min_value=0)

        submitted = st.form_submit_button("💾 Save Section 1")
        if submitted:
            data = {
                "Name": name,
                "BirthDate": str(birth_date),
                "Gender": gender,
                "Education": education,
                "YearsFarming": years_farming,
            }
            save_response(holder_id, "section_1", data)
            st.toast("Section 1 saved ✅")


# --------------------------
# Section 2: Holding Labour
# --------------------------
def holding_labour_form(holder_id):
    st.subheader("Section 2: Holding Labour")

    with st.form(key=f"holding_labour_form_{holder_id}", clear_on_submit=False):
        st.markdown("**From August 1, 2024 to July 31, 2025**")

        perm_male = st.number_input("Permanent Male Workers", min_value=0)
        perm_female = st.number_input("Permanent Female Workers", min_value=0)
        temp_male = st.number_input("Temporary Male Workers", min_value=0)
        temp_female = st.number_input("Temporary Female Workers", min_value=0)
        non_bahamian = st.number_input("Number of Non-Bahamian Workers", min_value=0)
        work_permit = st.selectbox("Did any workers have work permits?", ["Yes", "No", "Not Applicable"])
        volunteer = st.selectbox("Any volunteer (unpaid) workers?", ["Yes", "No", "Not Applicable"])
        contracted = st.selectbox("Used agricultural contracted services?", ["Yes", "No", "Not Applicable"])

        submitted = st.form_submit_button("💾 Save Section 2")
        if submitted:
            data = {
                "PermanentMale": perm_male,
                "PermanentFemale": perm_female,
                "TemporaryMale": temp_male,
                "TemporaryFemale": temp_female,
                "NonBahamian": non_bahamian,
                "WorkPermit": work_permit,
                "Volunteer": volunteer,
                "ContractedServices": contracted,
            }
            save_response(holder_id, "section_2", data)
            st.toast("Section 2 saved ✅")


# --------------------------
# Sidebar Navigation
# --------------------------
def survey_sidebar(holder_id):
    st.sidebar.title("Survey Navigation")

    section = st.sidebar.radio(
        "Go to section:",
        ["Section 1: Holder Information", "Section 2: Holding Labour"],
        key=f"section_nav_{holder_id}"
    )

    st.session_state["active_section"] = section

    # Stable section display
    if section.startswith("Section 1"):
        holder_information_form(holder_id)
    elif section.startswith("Section 2"):
        holding_labour_form(holder_id)
