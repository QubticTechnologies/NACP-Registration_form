# census_app/modules/holder_dashboard.py

import streamlit as st
from sqlalchemy import text
from datetime import date
import pandas as pd
from census_app.db import engine
from census_app.config import (
    HOLDERS_TABLE,
    HOLDER_SURVEY_PROGRESS_TABLE,
    TOTAL_SURVEY_SECTIONS
)
from census_app.modules.holder_register import register_holder, get_holder_name,get_holder_id
from census_app.modules.survey_sections import show_regular_survey_section
from census_app.modules.survey_sidebar import survey_sidebar
from census_app.modules.holding_labour_form import run_holding_labour_survey
from census_app.helpers import calculate_age

# ----------------- GIS Location Widget -----------------
def holder_location_widget(holder_id):
    """Display and update holder's GIS location using map + inputs."""
    with engine.connect() as conn:
        loc = conn.execute(
            text("SELECT latitude, longitude FROM holders WHERE id=:hid"),
            {"hid": holder_id}
        ).fetchone()

    holder_lat = loc[0] if loc else 0.0
    holder_lon = loc[1] if loc else 0.0

    st.subheader("📍 Holder Location")
    df = pd.DataFrame([[holder_lat, holder_lon]], columns=["lat", "lon"])
    st.map(df, zoom=10)

    st.write("Update your coordinates:")
    st.info("Drag the pin on the map to update location (approximate, then fine-tune below).")

    holder_lat = st.number_input("Latitude", value=holder_lat, step=0.000001)
    holder_lon = st.number_input("Longitude", value=holder_lon, step=0.000001)

    if st.button("Save Location", key=f"save_loc_{holder_id}"):
        if -90 <= holder_lat <= 90 and -180 <= holder_lon <= 180:
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE holders SET latitude=:lat, longitude=:lon WHERE id=:hid"),
                    {"lat": holder_lat, "lon": holder_lon, "hid": holder_id}
                )
            st.success("📌 Location saved successfully!")
            st.rerun()
        else:
            st.error("⚠️ Coordinates are out of valid range.")


# ----------------- Holder Dashboard -----------------
def holder_dashboard():
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.error("You must be logged in to access the dashboard.")
        return

    user_id = st.session_state["user"]["id"]

    # Fetch all holders for this user
    try:
        with engine.connect() as conn:
            holders = conn.execute(
                text(f"SELECT * FROM {HOLDERS_TABLE} WHERE owner_id=:uid ORDER BY id"),
                {"uid": user_id}
            ).mappings().all()
    except Exception as e:
        st.error(f"Error fetching holders: {e}")
        return

    st.sidebar.header("Your Holders")

    if holders:
        # Holder selection
        holder_options = {f"{h['name']} (ID: {h['id']})": h['id'] for h in holders}
        select_key = "holder_selectbox_dashboard"
        selected_holder_name = st.sidebar.selectbox(
            "Select Holder", options=list(holder_options.keys()), key=select_key
        )
        selected_holder_id = holder_options[selected_holder_name]
        st.session_state["selected_holder_id"] = selected_holder_id

        # Display holder name
        name = get_holder_name(selected_holder_id)
        if name:
            st.sidebar.markdown(
                f"<h4 style='text-align:center; font-weight:bold;'>{name}</h4>",
                unsafe_allow_html=True
            )
            st.sidebar.markdown("---")

        # ---------------- Sidebar + Survey ----------------
        survey_sidebar(holder_id=selected_holder_id, prefix="holder_dashboard")

        # ---------------- Dashboard Actions ----------------
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("View / Edit Holder Info"):
                register_holder(edit_holder_id=selected_holder_id)

        with col3:
            if st.button("Add New Holder"):
                register_holder()

        # ---------------- GIS Location ----------------
        holder_location_widget(selected_holder_id)

        # ---------------- Age Info ----------------
        try:
            with engine.connect() as conn:
                dob_row = conn.execute(
                    text(f"SELECT date_of_birth FROM {HOLDERS_TABLE} WHERE id=:hid"),
                    {"hid": selected_holder_id}
                ).scalar()
            if dob_row:
                if isinstance(dob_row, str):
                    dob_row = date.fromisoformat(dob_row)
                age = calculate_age(dob_row)
                st.sidebar.info(f"Holder Age: {age} years")
        except Exception as e:
            st.sidebar.warning(f"Could not fetch holder age: {e}")

        # ---------------- Render Selected Section ----------------
        current_section = st.session_state.get("next_survey_section", 1)
        if current_section <= TOTAL_SURVEY_SECTIONS:
            show_regular_survey_section(section_id=current_section, holder_id=selected_holder_id)
        else:
            run_holding_labour_survey(holder_id=selected_holder_id)

    else:
        st.info("You have no holders yet.")
        if st.button("Register First Holder"):
            register_holder()

    # ---------------- Logout ----------------
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        keys_to_keep = ["page", "next_survey_section"]
        for key in list(st.session_state.keys()):
            if key not in keys_to_keep:
                del st.session_state[key]
        st.session_state["user"] = None
        st.success("You have been logged out.")
        st.rerun()
