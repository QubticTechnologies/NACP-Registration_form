import sys
import os
import streamlit as st
import pandas as pd
from sqlalchemy import text

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# --- DB & Config ---
from census_app.db import engine
from census_app.config import USERS_TABLE, TOTAL_SURVEY_SECTIONS

# --- Lazy imports ---
from census_app.modules.auth import login_user, register_user, logout_user, create_holder_for_user
from census_app.modules.admin_auth import login_admin
from census_app.modules.role_sidebar import role_sidebar
from census_app.modules.dashboards import holder_dashboard, agent_dashboard
from census_app.modules.admin_dashboard.dashboard import admin_dashboard
from census_app.modules.survey_sidebar import survey_sidebar
from census_app.modules.general_info_form import general_info_form

# --- Page Config ---
st.set_page_config(page_title="AGRI_CENSUS SYSTEM", layout="wide")

# --- Session Defaults ---
st.session_state.setdefault("user", None)
st.session_state.setdefault("holder_id", None)
st.session_state.setdefault("logged_out", False)

# --- Helper ---
def get_user_status(user_id):
    """Return the approval status of a user."""
    try:
        with engine.connect() as conn:
            return conn.execute(
                text(f"SELECT status FROM {USERS_TABLE} WHERE id=:uid"),
                {"uid": user_id}
            ).scalar()
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

# --- Logout Handling ---
if st.session_state.get("logged_out"):
    st.session_state["user"] = None
    st.session_state["holder_id"] = None
    st.session_state["logged_out"] = False
    st.experimental_set_query_params()
    st.rerun()

# --- Not logged in ---
if st.session_state["user"] is None:
    choice = st.sidebar.radio("Login Type", ["Agent/Farmer", "Admin"])
    if choice == "Agent/Farmer":
        action = st.sidebar.radio("Action", ["Login", "Register"])
        if action == "Login":
            login_user()
        else:
            register_user()
    else:
        login_admin()

# --- Logged in ---
else:
    user = st.session_state["user"]
    role = user["role"].lower()
    user_id = user["id"]

    st.sidebar.success(f"✅ Logged in as {user['username']} ({role})")
    logout_user()  # keep logout button in sidebar

    # ---------------- Admin ----------------
    if role == "admin":
        # Full admin dashboard: approvals, bulk actions, graphs, reports, GI review
        admin_dashboard()

    # ---------------- Holder ----------------
    elif role == "holder":
        holder_id = create_holder_for_user(user_id, user["username"])
        st.session_state["holder_id"] = holder_id

        # Check approval status
        status = get_user_status(user_id)
        if status != "approved":
            st.error("🚫 Your account is not approved yet. Please wait for admin approval.")
            st.stop()

        st.title("Holder Dashboard")

        # --- General Information Check ---
        with engine.connect() as conn:
            completed_count = conn.execute(
                text("SELECT COUNT(*) FROM general_information WHERE holder_id=:hid"),
                {"hid": holder_id}
            ).scalar()

        if completed_count == 0:
            st.warning("⚠️ Please complete your General Information before continuing.")
            form_completed = general_info_form(holder_id=holder_id)
            if form_completed:
                st.success("✅ General Information saved successfully. You may now continue.")
            st.stop()  # stop until general info completed

        # --- Survey sidebar + forms ---
        survey_sidebar(holder_id=holder_id, prefix=f"holder_{holder_id}")

        # --- Holder dashboard view ---
        holder_dashboard(holder_id)

        # --- Map of holdings ---
        try:
            with engine.connect() as conn:
                holdings = conn.execute(
                    text("""SELECT name, latitude, longitude
                            FROM holders
                            WHERE owner_id=:uid
                            AND latitude IS NOT NULL AND longitude IS NOT NULL"""),
                    {"uid": user_id}
                ).fetchall()

            if holdings:
                df_map = pd.DataFrame(holdings, columns=["name", "lat", "lon"])
                st.map(df_map[["lat", "lon"]], zoom=7)
                st.table(df_map)
            else:
                st.info("No farm locations found. Showing default map.")
                df_map = pd.DataFrame([[25.0343, -77.3963]], columns=["lat", "lon"])
                st.map(df_map, zoom=7)
        except Exception as e:
            st.warning(f"Could not load holdings map: {e}")

    # ---------------- Agent ----------------
    else:
        role_sidebar(user_role=role)
