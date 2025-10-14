import sys
import os
import streamlit as st
import pandas as pd
import requests
from sqlalchemy import text
from datetime import date
from streamlit_js_eval import get_geolocation

# Add current directory for imports
sys.path.append(os.path.dirname(__file__))

# --- DB & Config ---
from census_app.db import engine
from census_app.config import USERS_TABLE, HOLDERS_TABLE, TOTAL_SURVEY_SECTIONS

# --- Lazy Imports to avoid circular imports ---
def _import_auth():
    from census_app.modules.auth import login_user, register_user, logout_user, create_holder_for_user
    return login_user, register_user, logout_user, create_holder_for_user

def _import_role_sidebar():
    from census_app.modules.role_sidebar import role_sidebar
    return role_sidebar

def _import_dashboards():
    from census_app.modules.dashboards import holder_dashboard, agent_dashboard
    from census_app.modules.admin_dashboard.dashboard import admin_dashboard
    return holder_dashboard, agent_dashboard, admin_dashboard

def _import_survey_sidebar():
    from census_app.modules.survey_sidebar import survey_sidebar
    return survey_sidebar

# --- Dynamic Imports ---
login_user, register_user, logout_user, create_holder_for_user = _import_auth()
role_sidebar = _import_role_sidebar()
holder_dashboard, agent_dashboard, admin_dashboard = _import_dashboards()
survey_sidebar = _import_survey_sidebar()

# --- Survey Forms ---
from census_app.modules.household_information import household_information
from census_app.modules.holding_labour_form import holding_labour_form
from census_app.modules.holder_information_form import holder_information_form
from census_app.helpers import calculate_age

# --- Streamlit Config ---
st.set_page_config(page_title="🌾 Agri Census System", layout="wide")

# --- Session Defaults ---
st.session_state.setdefault("user", None)
st.session_state.setdefault("holder_id", None)
st.session_state.setdefault("logged_out", False)
st.session_state.setdefault("current_section", 1)
st.session_state.setdefault("holder_form_data", {})
st.session_state.setdefault("labour_form_data", {})
st.session_state.setdefault("household_form_data", {})

# -----------------------------
# Helper Functions
# -----------------------------
def get_user_status(user_id: int):
    try:
        with engine.connect() as conn:
            return conn.execute(
                text(f"SELECT status FROM {USERS_TABLE} WHERE id=:uid"),
                {"uid": user_id}
            ).scalar()
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

# -----------------------------
# GIS Location Widget
# -----------------------------
def holder_location_widget(holder_id):
    st.subheader("📍 Farm Location")
    st.info("Allow browser to detect GPS for accurate location or enter manually.")

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

    # Auto Detect Location
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
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        street_address = data.get("display_name", "Address not found")
    except Exception:
        street_address = "Unable to fetch address"

    st.text_input("🏠 Street / Address (display only)", value=street_address, disabled=True)

    # Google Maps link
    if holder_lat and holder_lon:
        maps_url = f"https://www.google.com/maps?q={holder_lat},{holder_lon}"
        st.markdown(f"[🗺️ View on Google Maps]({maps_url})")

    # Save to DB
    if st.button("💾 Save Farm Location", key=f"save_loc_btn_{holder_id}"):
        if -90 <= holder_lat <= 90 and -180 <= holder_lon <= 180:
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE holders SET latitude=:lat, longitude=:lon WHERE holder_id=:hid"),
                    {"lat": holder_lat, "lon": holder_lon, "hid": holder_id}
                )
            st.success("✅ Location saved successfully!")
            st.experimental_rerun()
        else:
            st.error("⚠️ Invalid coordinates. Please check values.")

# -----------------------------
# Main Login & Flow
# -----------------------------
st.sidebar.title("🌱 Agri Census System")

# Reset after logout
if st.session_state.get("logged_out"):
    st.session_state.update({"user": None, "holder_id": None, "logged_out": False})
    st.experimental_set_query_params()
    st.experimental_rerun()

# Login Flow
if st.session_state["user"] is None:
    login_choice = st.sidebar.radio("Login Type", ["Agent/Farmer", "Admin"])
    if login_choice == "Agent/Farmer":
        action = st.sidebar.radio("Action", ["Login", "Register"])
        if action == "Login":
            login_user()
        else:
            register_user()
    else:
        from census_app.modules.admin_auth import login_admin
        login_admin()

# Logged-In Flow
else:
    user = st.session_state["user"]
    role = user["role"].lower()
    user_id = user["id"]

    st.sidebar.success(f"✅ Logged in as {user['username']} ({role})")
    logout_user()

    holder_id = None
    if role == "holder":
        holder_id = create_holder_for_user(user_id, user["username"])
        st.session_state["holder_id"] = holder_id

        # Approval check
        status = get_user_status(user_id)
        if status != "approved":
            st.error("🚫 Your account is not yet approved by admin.")
            st.stop()

        # ----------- MAP AT THE TOP -----------
        holder_location_widget(holder_id)

        # Validate coordinates
        with engine.connect() as conn:
            loc = conn.execute(
                text("SELECT latitude, longitude FROM holders WHERE holder_id=:hid"),
                {"hid": holder_id}
            ).fetchone()
        if not loc or loc[0] is None or loc[1] is None:
            st.warning("⚠️ Please set your farm location to continue.")
            st.stop()

        # ----------- SURVEY NAVIGATION -----------
        if st.session_state["current_section"] < 1:
            st.session_state["current_section"] = 1

        survey_sidebar(holder_id=holder_id)
        st.divider()

        # Navigation buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅ Back", key=f"back_{holder_id}") and st.session_state["current_section"] > 1:
                st.session_state["current_section"] -= 1
                st.experimental_rerun()
        with col3:
            if st.button("Next ➡", key=f"next_{holder_id}") and st.session_state["current_section"] < TOTAL_SURVEY_SECTIONS:
                st.session_state["current_section"] += 1
                st.experimental_rerun()

        # Render current section dynamically
        current = st.session_state["current_section"]
        st.markdown(f"### Section {current} of {TOTAL_SURVEY_SECTIONS}")
        if current == 1:
            holder_information_form(holder_id)
        elif current == 2:
            holding_labour_form(holder_id)
        elif current == 3:
            household_information(holder_id)

        # ----------- HOLDER DASHBOARD -----------
        st.divider()
        st.title("📊 Holder Dashboard")
        #holder_dashboard(holder_id)

        # Age info
        try:
            with engine.connect() as conn:
                dob_row = conn.execute(
                    text(f"SELECT date_of_birth FROM {HOLDERS_TABLE} WHERE holder_id=:hid"),
                    {"hid": holder_id}
                ).scalar()
            if dob_row:
                if isinstance(dob_row, str):
                    dob_row = date.fromisoformat(dob_row)
                st.sidebar.info(f"🎂 Age: {calculate_age(dob_row)} years")
        except Exception as e:
            st.sidebar.warning(f"Could not fetch holder age: {e}")

    # Agent/Admin Menus
    role_sidebar(user_role=role, holder_id=holder_id)
