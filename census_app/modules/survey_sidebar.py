import streamlit as st
from census_app.modules.holder_information_form import holder_information_form
from census_app.modules.holding_labour_form import holding_labour_form
from census_app.modules.survey_helpers import get_completed_sections

# ---------------- Survey Sections ----------------
SURVEY_SECTIONS = {
    1: {"label": "Holder Information", "func": holder_information_form, "needs_holder_id": False},
    2: {"label": "Holding Labour Form", "func": holding_labour_form, "needs_holder_id": True},
}

# ---------------- Survey Sidebar ----------------
def survey_sidebar(holder_id=None, prefix=""):
    """
    Render the survey sidebar with progress, section buttons, and current survey section.
    Sidebar will always stay visible.
    """

    st.sidebar.markdown("## Survey Progress")

    if holder_id is None:
        st.sidebar.info("Survey progress available only for a selected holder.")
        return

    # ---------------- Holder Info Header ----------------
    st.sidebar.markdown(
        f"<h4 style='text-align:center; font-weight:bold;'>Holder ID: {holder_id}</h4>",
        unsafe_allow_html=True
    )
    st.sidebar.markdown("---")

    # ---------------- Completed Sections ----------------
    completed_sections = set(get_completed_sections(holder_id))
    completed_sections = {s for s in completed_sections if s in SURVEY_SECTIONS}

    # ---------------- Determine Next Section ----------------
    state_key_next = f"{prefix}_next_section"
    if state_key_next not in st.session_state:
        # Automatically select the first incomplete section
        for sec_id in sorted(SURVEY_SECTIONS.keys()):
            if sec_id not in completed_sections:
                st.session_state[state_key_next] = sec_id
                break
        else:
            st.session_state[state_key_next] = max(SURVEY_SECTIONS.keys())

    next_section = st.session_state[state_key_next]

    # ---------------- Progress Bar ----------------
    total_steps = len(SURVEY_SECTIONS)
    progress_pct = len(completed_sections) / total_steps if total_steps else 0
    st.sidebar.progress(progress_pct)

    # ---------------- Section Buttons ----------------
    for sec_id, sec in SURVEY_SECTIONS.items():
        if sec_id in completed_sections:
            label = f"{sec['label']} ✅"
            color = "#28a745"
        elif sec_id == next_section:
            label = f"➡️ {sec['label']}"
            color = "#0d6efd"
        else:
            label = sec['label']
            color = "#6c757d"

        btn_key = f"{prefix}_sec_btn_{sec_id}"
        clicked = st.sidebar.button(label, key=btn_key)

        if clicked:
            st.session_state[state_key_next] = sec_id

        # Button CSS
        st.sidebar.markdown(f"""
            <style>
            div.stButton > button[key="{btn_key}"] {{
                background-color: {color};
                color: white;
            }}
            </style>
        """, unsafe_allow_html=True)

    # ---------------- Render Current Section ----------------
    current_section = SURVEY_SECTIONS.get(st.session_state[state_key_next])
    if current_section:
        try:
            if current_section["needs_holder_id"]:
                # Pass prefix to prevent duplicate keys
                current_section["func"](holder_id=holder_id, prefix=prefix)
            else:
                current_section["func"]()
        except Exception as e:
            st.error(f"Error rendering section: {e}")
