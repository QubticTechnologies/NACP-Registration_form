import streamlit as st
from census_app.modules.admin_auth import admin_sidebar  # ✅ absolute import


# --- Page Config ---
st.set_page_config(page_title="NACP - Admin Dashboard", layout="wide")

# --- Title ---
st.title("👨‍💼 NACP - Admin Dashboard")

# --- Sidebar ---
admin_sidebar()

# --- Dashboard Content ---
if st.session_state.get("logged_in") and st.session_state.get("user_role") == "Admin":
    st.success("✅ Welcome to the Admin Dashboard!")

    st.subheader("Admin Functions")
    st.write("Here you can manage users, assign agents, and monitor survey progress.")

    # Example placeholders for functionality
    st.button("➕ Approve New Users")
    st.button("👷 Assign Agents to Farmers")
    st.button("📊 View Survey Reports")

else:
    st.warning("🔒 Please log in as an Admin to access this dashboard.")
