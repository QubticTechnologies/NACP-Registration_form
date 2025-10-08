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
from census_app.modules.auth import login_user, register_user, logout_user
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
st.session_state.setdefault("lat", None)
st.session_state.setdefault("lon", None)
st.session_state.setdefault("gi_completed", False)

# --- Helper: safe rerun for old/new Streamlit ---
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

# --- Helper Function ---
def get_user_status(user_id):
    """Return the approval status of a user."""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT status FROM {USERS_TABLE} WHERE id=:uid"),
                {"uid": user_id}
            ).mappings().fetchone()
            return result["status"] if result else None
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

# --- Ensure holder exists and return holder_id ---
def create_holder_for_user(user_id, username):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT holder_id FROM holders WHERE owner_id=:uid"),
            {"uid": user_id}
        ).mappings().fetchone()
        if result:
            return result["holder_id"]

        # Create new holder
        conn.execute(
            text("INSERT INTO holders (owner_id, name) VALUES (:uid, :name)"),
            {"uid": user_id, "name": username}
        )
        result = conn.execute(
            text("SELECT holder_id FROM holders WHERE owner_id=:uid"),
            {"uid": user_id}
        ).mappings().fetchone()
        return result["holder_id"]

# --- Logout Handling ---
if st.session_state.get("logged_out"):
    st.session_state.update({
        "user": None,
        "holder_id": None,
        "lat": None,
        "lon": None,
        "gi_completed": False,
        "logged_out": False
    })
    st.experimental_set_query_params()
    safe_rerun()

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
    logout_user()  # Sidebar logout button

    # ---------------- Admin ----------------
    if role == "admin":
        admin_dashboard()  # Admin dashboard fully restored

    # ---------------- Holder ----------------
    elif role == "holder":
        holder_id = create_holder_for_user(user_id, user["username"])
        st.session_state["holder_id"] = holder_id

        # Approval check
        status = get_user_status(user_id)
        if status != "approved":
            st.error("🚫 Your account is not approved yet. Please wait for admin approval.")
            st.stop()

        st.title("Holder Dashboard")

        # --- Step 1: Farm location ---
        if st.session_state["lat"] is None or st.session_state["lon"] is None:
            st.subheader("Step 1: Enter Your Farm Location")
            lat = st.number_input("Latitude", value=25.0343, format="%.6f", step=0.0001)
            lon = st.number_input("Longitude", value=-77.3963, format="%.6f", step=0.0001)
            st.map(pd.DataFrame([[lat, lon]], columns=["lat", "lon"]), zoom=10)

            if st.button("Submit Location"):
                st.session_state["lat"] = lat
                st.session_state["lon"] = lon
                with engine.connect() as conn:
                    conn.execute(
                        text("""UPDATE holders
                                SET latitude=:lat, longitude=:lon
                                WHERE holder_id=:hid"""),
                        {"lat": lat, "lon": lon, "hid": holder_id}
                    )
                st.success("✅ Location saved!")
                safe_rerun()

        # --- Step 2: General Information ---
        elif not st.session_state["gi_completed"]:
            with engine.connect() as conn:
                completed_count = conn.execute(
                    text("SELECT COUNT(*) FROM general_information WHERE holder_id=:hid"),
                    {"hid": holder_id}
                ).scalar()

            if completed_count == 0:
                st.subheader("Step 2: Complete General Information")
                form_completed = general_info_form(holder_id=holder_id)
                if form_completed:
                    st.session_state["gi_completed"] = True
                    st.success("✅ General Information completed!")
                    safe_rerun()
            else:
                st.session_state["gi_completed"] = True

        # --- Step 3: Survey + Holder Dashboard ---
        else:
            st.subheader("Step 3: Survey")
            survey_sidebar(holder_id=holder_id, prefix=f"holder_{holder_id}")
            holder_dashboard(holder_id)

    # ---------------- Agent ----------------
    else:
        role_sidebar(user_role=role)
