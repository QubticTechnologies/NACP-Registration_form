import streamlit as st
from sqlalchemy import text
from census_app.db import engine
import pandas as pd
import datetime

# ---------------- Options ----------------
SEX_OPTIONS = ["Male", "Female", "Other"]
MARITAL_STATUS_OPTIONS = [
    "Single", "Married", "Divorced", "Separated",
    "Widowed", "Common-law", "Prefer not to disclose"
]
EDUCATION_OPTIONS = [
    "No Schooling", "Primary", "Junior Secondary",
    "Senior Secondary", "Undergraduate", "Masters",
    "Doctorate", "Vocational", "Professional Designation"
]
YES_NO = ["Yes", "No"]
OCCUPATION_OPTIONS = ["Agriculture", "Other"]

# ---------------- Form Function ----------------
def holder_information_form():
    """
    Section 1: Holder Information
    Collects up to 3 holders (Holder 1 = Main) and stores them in the holders table.
    """
    st.header("Section 1: Holder Information")

    holders_data = []

    for i in range(1, 4):  # Holder 1 (Main), Holder 2, Holder 3
        st.subheader(f"Holder {i}{' - Main' if i == 1 else ''}")

        full_name = st.text_input(f"Full Name (Holder {i})", key=f"name_{i}", max_chars=100)
        sex = st.selectbox(f"Sex (Holder {i})", SEX_OPTIONS, key=f"sex_{i}")
        dob = st.date_input(
            f"Date of Birth (Holder {i})",
            key=f"dob_{i}",
            format="DD/MM/YYYY",
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date.today()
        )
        nationality = st.selectbox(f"Nationality (Holder {i})", ["Bahamian", "Other"], key=f"nat_{i}")
        nationality_other = ""
        if nationality == "Other":
            nationality_other = st.text_input(f"Specify Nationality (Holder {i})", key=f"nat_other_{i}", max_chars=100)

        marital_status = st.selectbox(f"Marital Status (Holder {i})", MARITAL_STATUS_OPTIONS, key=f"mar_{i}")
        education = st.selectbox(f"Highest Level of Education (Holder {i})", EDUCATION_OPTIONS, key=f"edu_{i}")
        ag_training = st.radio(f"Agricultural Education/Training (Holder {i})", YES_NO, key=f"train_{i}")
        ag_training_val = "Yes" if ag_training == "Yes" else "No"

        primary_occupation = st.selectbox(f"Primary Occupation (Holder {i})", OCCUPATION_OPTIONS, key=f"primocc_{i}")
        primary_occupation_other = ""
        if primary_occupation == "Other":
            primary_occupation_other = st.text_input(
                f"Specify Primary Occupation (Holder {i})", key=f"primocc_other_{i}", max_chars=100
            )
        secondary_occupation = st.text_input(f"Secondary Occupation (Holder {i})", key=f"secocc_{i}", max_chars=100)

        # Collect data
        holders_data.append({
            "holder_number": i,
            "full_name": full_name,
            "sex": sex,
            "date_of_birth": dob,
            "nationality": nationality,
            "nationality_other": nationality_other,
            "marital_status": marital_status,
            "highest_education": education,
            "agri_training": ag_training_val,
            "primary_occupation": primary_occupation,
            "primary_occupation_other": primary_occupation_other,
            "secondary_occupation": secondary_occupation
        })

    # ---------------- Preview Table ----------------
    st.subheader("Preview Entered Holder Information")
    df_preview = pd.DataFrame(holders_data)
    if not df_preview.empty:
        st.dataframe(df_preview[[
            "holder_number", "full_name", "sex", "date_of_birth",
            "nationality", "nationality_other", "marital_status",
            "highest_education", "agri_training",
            "primary_occupation", "primary_occupation_other",
            "secondary_occupation"
        ]])

    # ---------------- Save to Database ----------------
    if st.button("💾 Save Holder Information"):
        with engine.begin() as conn:
            for holder in holders_data:
                if holder["full_name"]:  # only save if name is provided
                    conn.execute(
                        text("""
                            INSERT INTO holders (
                                name, sex, date_of_birth,
                                nationality, nationality_other, marital_status,
                                highest_education, agri_training,
                                primary_occupation, primary_occupation_other,
                                secondary_occupation
                            )
                            VALUES (
                                :full_name, :sex, :date_of_birth,
                                :nationality, :nationality_other, :marital_status,
                                :highest_education, :agri_training,
                                :primary_occupation, :primary_occupation_other,
                                :secondary_occupation
                            )
                            ON CONFLICT(holder_id) DO UPDATE SET
                                name=EXCLUDED.name,
                                sex=EXCLUDED.sex,
                                date_of_birth=EXCLUDED.date_of_birth,
                                nationality=EXCLUDED.nationality,
                                nationality_other=EXCLUDED.nationality_other,
                                marital_status=EXCLUDED.marital_status,
                                highest_education=EXCLUDED.highest_education,
                                agri_training=EXCLUDED.agri_training,
                                primary_occupation=EXCLUDED.primary_occupation,
                                primary_occupation_other=EXCLUDED.primary_occupation_other,
                                secondary_occupation=EXCLUDED.secondary_occupation
                        """),
                        holder
                    )
        st.success("✅ Holder Information saved successfully!")
