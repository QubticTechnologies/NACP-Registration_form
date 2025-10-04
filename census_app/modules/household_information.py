import streamlit as st
from sqlalchemy import text
from census_app.db import engine
import pandas as pd

# ---------------- Options ----------------
RELATIONSHIP_OPTIONS = {
    1: "Spouse/Partner", 2: "Son", 3: "Daughter", 4: "In-Laws",
    5: "Grandchild", 6: "Parent/Parent-In-Law", 7: "Other Relative", 8: "Non-Relative"
}
SEX_OPTIONS = ["Male", "Female"]
EDUCATION_OPTIONS = {
    1: "No Schooling", 2: "Primary", 3: "Junior Secondary", 4: "Senior Secondary",
    5: "Undergraduate", 6: "Masters", 7: "Doctorate", 8: "Vocational", 9: "Professional Designation"
}
OCCUPATION_OPTIONS = {
    1: "Agriculture", 2: "Fishing", 3: "Professional/Technical", 4: "Administrative/Manager",
    5: "Sales", 6: "Customer Service", 7: "Tourism", 8: "Not Economically Active", 9: "Other"
}
WORKING_TIME_OPTIONS = {"N": "None", "F": "Full time", "P": "Part time", "P3": "1-3 months", "P6": "4-6 months", "P7": "7+ months"}

# ---------------- Household Information ----------------
def household_information(holder_id, holder_ids=[1, 2, 3]):
    st.header("Section 3 - Household Information")

    # ---------------- Summary Inputs per Holder ----------------
    inputs = []
    for holder_number in holder_ids:
        with st.expander(f"👤 Holder {holder_number} Household Summary", expanded=(holder_number == 1)):
            total_persons = st.number_input(f"Total persons living in household (including holder) - Holder {holder_number}",
                                            min_value=0, max_value=100, step=1, key=f"total_{holder_number}")

            # Age breakdown columns
            col1, col2 = st.columns(2)
            with col1:
                u14_male = st.number_input("Under 14 (Male)", 0, 100, 0, key=f"u14_male_{holder_number}")
                plus14_male = st.number_input("14+ (Male)", 0, 100, 0, key=f"14plus_male_{holder_number}")
            with col2:
                u14_female = st.number_input("Under 14 (Female)", 0, 100, 0, key=f"u14_female_{holder_number}")
                plus14_female = st.number_input("14+ (Female)", 0, 100, 0, key=f"14plus_female_{holder_number}")

            # Paid/Unpaid workers columns
            col3, col4 = st.columns(2)
            with col3:
                wm_paid = st.number_input("Work on holding (Male Paid)", 0, 100, 0, key=f"work_male_paid_{holder_number}")
                wm_unpaid = st.number_input("Work on holding (Male Unpaid)", 0, 100, 0, key=f"work_male_unpaid_{holder_number}")
            with col4:
                wf_paid = st.number_input("Work on holding (Female Paid)", 0, 100, 0, key=f"work_female_paid_{holder_number}")
                wf_unpaid = st.number_input("Work on holding (Female Unpaid)", 0, 100, 0, key=f"work_female_unpaid_{holder_number}")

            # Validation
            age_total = u14_male + u14_female + plus14_male + plus14_female
            if age_total > total_persons:
                st.warning(f"⚠️ Total persons ({total_persons}) is less than sum of age groups ({age_total}).")

            inputs.append({
                "holder_number": holder_number,
                "total_persons": total_persons,
                "u14_male": u14_male, "u14_female": u14_female,
                "plus14_male": plus14_male, "plus14_female": plus14_female,
                "wm_paid": wm_paid, "wm_unpaid": wm_unpaid,
                "wf_paid": wf_paid, "wf_unpaid": wf_unpaid
            })

    if st.button("💾 Save Household Summary"):
        with engine.begin() as conn:
            for row in inputs:
                conn.execute(text("""
                    INSERT INTO household_summary (
                        holdings_id, holder_number, total_persons,
                        persons_under_14_male, persons_under_14_female,
                        persons_14plus_male, persons_14plus_female,
                        persons_working_male_paid, persons_working_male_unpaid,
                        persons_working_female_paid, persons_working_female_unpaid
                    ) VALUES (
                        :holdings_id, :holder_number, :total_persons,
                        :u14_male, :u14_female,
                        :plus14_male, :plus14_female,
                        :wm_paid, :wm_unpaid,
                        :wf_paid, :wf_unpaid
                    )
                    ON CONFLICT (holdings_id, holder_number)
                    DO UPDATE SET
                        total_persons = EXCLUDED.total_persons,
                        persons_under_14_male = EXCLUDED.persons_under_14_male,
                        persons_under_14_female = EXCLUDED.persons_under_14_female,
                        persons_14plus_male = EXCLUDED.persons_14plus_male,
                        persons_14plus_female = EXCLUDED.persons_14plus_female,
                        persons_working_male_paid = EXCLUDED.persons_working_male_paid,
                        persons_working_male_unpaid = EXCLUDED.persons_working_male_unpaid,
                        persons_working_female_paid = EXCLUDED.persons_working_female_paid,
                        persons_working_female_unpaid = EXCLUDED.persons_working_female_unpaid;
                """), {**row, "holdings_id": holder_id})
        st.success("✅ Household Summary saved successfully!")

    # ---------------- Detailed Household Members ----------------
    st.subheader("Detailed Household Members")
    with engine.begin() as conn:
        members = conn.execute(text("""
            SELECT relationship_to_holder, sex, age, education_level,
                   primary_occupation, secondary_occupation, working_time_on_holding
            FROM household_information
            WHERE holder_id = :holder_id
        """), {"holder_id": holder_id}).fetchall()

    # Display existing members in table
    if members:
        df_members = pd.DataFrame([{
            "Relationship": RELATIONSHIP_OPTIONS[m.relationship_to_holder],
            "Sex": m.sex, "Age": m.age,
            "Education": EDUCATION_OPTIONS[m.education_level],
            "Primary Occupation": OCCUPATION_OPTIONS[m.primary_occupation],
            "Secondary Occupation": OCCUPATION_OPTIONS.get(m.secondary_occupation, "None"),
            "Work Time": WORKING_TIME_OPTIONS[m.working_time_on_holding]
        } for m in members])
        st.table(df_members)

    # Add new members
    existing_rels = {m.relationship_to_holder for m in members} if members else set()
    for rel_code, rel_label in RELATIONSHIP_OPTIONS.items():
        if rel_code in existing_rels:
            continue
        st.markdown(f"### Add {rel_label}")
        with st.form(f"household_member_form_{rel_code}", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                sex = st.radio("Sex", SEX_OPTIONS, horizontal=True)
                age = st.number_input("Age (as of July 31, 2025)", 0, 100, 0)
                edu = st.selectbox("Education Level", options=list(EDUCATION_OPTIONS.keys()),
                                   format_func=lambda x: f"{x} - {EDUCATION_OPTIONS[x]}")
            with col2:
                primary_occ = st.selectbox("Primary Occupation", options=list(OCCUPATION_OPTIONS.keys()),
                                           format_func=lambda x: f"{x} - {OCCUPATION_OPTIONS[x]}")
                secondary_occ = st.selectbox("Secondary Occupation (optional)",
                                             options=[None] + list(OCCUPATION_OPTIONS.keys()),
                                             format_func=lambda x: f"{x} - {OCCUPATION_OPTIONS[x]}" if x else "None")
                work_time = st.selectbox("Working Time on Holding", options=list(WORKING_TIME_OPTIONS.keys()),
                                         format_func=lambda x: f"{x} - {WORKING_TIME_OPTIONS[x]}")
            submitted = st.form_submit_button("Add Member")
            if submitted:
                with engine.begin() as conn:
                    conn.execute(text("""
                        INSERT INTO household_information
                        (holder_id, relationship_to_holder, sex, age, education_level,
                         primary_occupation, secondary_occupation, working_time_on_holding)
                        VALUES (:holder_id, :rel, :sex, :age, :edu, :primary_occ, :secondary_occ, :work_time)
                    """), {
                        "holder_id": holder_id, "rel": rel_code, "sex": sex, "age": age, "edu": edu,
                        "primary_occ": primary_occ, "secondary_occ": secondary_occ, "work_time": work_time
                    })
                st.success(f"✅ {rel_label} added successfully")
