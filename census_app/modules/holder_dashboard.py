import streamlit as st
import pandas as pd
import requests
from sqlalchemy import text
from streamlit_js_eval import get_geolocation
from datetime import date
from census_app.db import engine
from census_app.config import HOLDERS_TABLE, TOTAL_SURVEY_SECTIONS
from census_app.modules.holder_information_form import holder_information_form
from census_app.modules.survey_sections import show_regular_survey_section
from census_app.helpers import calculate_age

# Optional labour survey
try:
    from census_app.modules.holding_labour_form import run_holding_labour_survey
except ImportError:
    run_holding_labour_survey = None


# -----------------------------
# Location Widget
# -----------------------------
def holder_location_widget(holder_id):
    st.subheader("📍 Confirm Your Farm Location")
    st.info("Allow browser location access for best accuracy or enter manually.")

    # Fetch stored coordinates
    with engine.connect() as conn:
        loc = conn.execute(
            text("SELECT latitude, longitude FROM holders WHERE holder_id=:hid"),
            {"hid": holder_id}
        ).fetchone()
    holder_lat = loc[0] if loc and loc[0] is not None else 25.0343
    holder_lon = loc[1] if loc and loc[1] is not None else -77.3963

    # Map preview
    st.map(pd.DataFrame([[holder_lat, holder_lon]], columns=["lat", "lon"]), zoom=15)

    # Manual entry
    col1, col2 = st.columns(2)
    with col1:
        holder_lat = st.number_input(
            "Latitude",
            value=float(st.session_state.get(f"holder_lat_{holder_id}", holder_lat)),
            step=0.000001,
            key=f"lat_input_{holder_id}"
        )
    with col2:
        holder_lon = st.number_input(
            "Longitude",
            value=float(st.session_state.get(f"holder_lon_{holder_id}", holder_lon)),
            step=0.000001,
            key=f"lon_input_{holder_id}"
        )

    # Browser Auto-Detect
    if st.button("🎯 Auto Detect Location", key=f"auto_loc_btn_{holder_id}"):
        with st.spinner("Detecting your location..."):
            loc = get_geolocation()
            if loc and "coords" in loc:
                holder_lat = loc["coords"]["latitude"]
                holder_lon = loc["coords"]["longitude"]
                accuracy = loc["coords"].get("accuracy", "N/A")
                st.session_state[f"holder_lat_{holder_id}"] = holder_lat
                st.session_state[f"holder_lon_{holder_id}"] = holder_lon
                st.success(f"✅ GPS Detected: {holder_lat:.6f}, {holder_lon:.6f} (±{accuracy}m)")
                st.map(pd.DataFrame([[holder_lat, holder_lon]], columns=["lat", "lon"]), zoom=17)
            else:
                st.error("⚠️ Could not access browser GPS. Check permissions.")

    # Reverse geocode
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={holder_lat}&lon={holder_lon}&zoom=18&addressdetails=1"
        headers = {"User-Agent": "AgriCensusApp/1.0"}
        data = requests.get(url, headers=headers, timeout=10).json()
        street_address = data.get("display_name", "Address not found")
    except Exception:
        street_address = "Unable to fetch address"

    st.text_input("🏠 Street / Address (auto-filled)", value=street_address, disabled=True)

    # Google Maps link
    if holder_lat and holder_lon:
        st.markdown(f"[🗺️ View on Google Maps](https://www.google.com/maps?q={holder_lat},{holder_lon})")

    # Save to DB
    if st.button("💾 Save Farm Location", key=f"save_loc_btn_{holder_id}"):
        if -90 <= holder_lat <= 90 and -180 <= holder_lon <= 180:
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE holders SET latitude=:lat, longitude=:lon WHERE holder_id=:hid"),
                    {"lat": holder_lat, "lon": holder_lon, "hid": holder_id}
                )
            st.success("📌 Location saved successfully!")
            st.rerun()
        else:
            st.error("⚠️ Invalid coordinates.")


# -----------------------------
# Holder Dashboard
# -----------------------------
def holder_dashboard(holder_id):
    """
    Main dashboard for holder users.

    Args:
        holder_id: The ID of the holder to display dashboard for
    """
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.error("You must be logged in to access the dashboard.")
        return

    user_id = st.session_state["user"]["id"]

    # Fetch holders for user
    try:
        with engine.connect() as conn:
            holders = conn.execute(
                text(f"SELECT * FROM {HOLDERS_TABLE} WHERE owner_id=:uid ORDER BY holder_id"),
                {"uid": user_id}
            ).mappings().all()
    except Exception as e:
        st.error(f"Error fetching holders: {e}")
        return

    # No holders exist
    if not holders:
        st.info("You have no registered holders yet.")
        if st.button("➕ Add First Holder"):
            with engine.begin() as conn:
                result = conn.execute(
                    text("INSERT INTO holders (owner_id, name) VALUES (:uid, :name)"),
                    {"uid": user_id, "name": "New Holder"}
                )
                new_holder_id = result.lastrowid
            st.success("✅ Holder created successfully!")
            st.rerun()
        return

    # Select the holder - validate it exists
    selected_holder = next((h for h in holders if h["holder_id"] == holder_id), None)
    if not selected_holder:
        st.warning(f"⚠️ Holder ID {holder_id} not found or doesn't belong to you.")
        selected_holder = holders[0]  # Default to first holder

    st.sidebar.markdown(
        f"<h4 style='text-align:center; font-weight:bold;'>{selected_holder['name']}</h4>",
        unsafe_allow_html=True
    )
    st.sidebar.markdown("---")

    # Confirm location
    st.header("🌾 Farm Location Confirmation")
    holder_location_widget(selected_holder["holder_id"])

    # Survey section
    st.subheader("📋 Survey Section")
    current_section = st.session_state.get("next_survey_section", 1)
    if current_section <= TOTAL_SURVEY_SECTIONS:
        show_regular_survey_section(section_id=current_section, holder_id=selected_holder["holder_id"])
    elif run_holding_labour_survey:
        run_holding_labour_survey(holder_id=selected_holder["holder_id"])

    # Age info
    try:
        with engine.connect() as conn:
            dob_row = conn.execute(
                text(f"SELECT date_of_birth FROM {HOLDERS_TABLE} WHERE holder_id=:hid"),
                {"hid": selected_holder["holder_id"]}
            ).scalar()
        if dob_row:
            if isinstance(dob_row, str):
                dob_row = date.fromisoformat(dob_row)
            st.sidebar.info(f"🎂 Age: {calculate_age(dob_row)} years")
    except Exception as e:
        st.sidebar.warning(f"Could not fetch holder age: {e}")

    # Holder actions
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✏️ Edit Holder Info", key=f"edit_holder_{selected_holder['holder_id']}"):
            holder_information_form(selected_holder["holder_id"])
    with col3:
        if st.button("➕ Add New Holder", key=f"add_new_holder_{selected_holder['holder_id']}"):
            with engine.begin() as conn:
                result = conn.execute(
                    text("INSERT INTO holders (owner_id, name) VALUES (:uid, :name)"),
                    {"uid": user_id, "name": "New Holder"}
                )
                new_holder_id = result.lastrowid
            holder_information_form(new_holder_id)

    # Logout
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", key=f"logout_{selected_holder['holder_id']}"):
        st.session_state.clear()
        st.success("👋 Logged out successfully.")
        st.rerun()


# -----------------------------
# Agent Dashboard (placeholder)
# -----------------------------
def agent_dashboard():
    """Dashboard for agent users."""
    st.header("🕵️ Agent Dashboard")
    st.info("Agent dashboard functionality coming soon...")