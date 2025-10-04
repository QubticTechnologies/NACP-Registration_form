# admin_app.py
import streamlit as st
from census_app.modules.admin_auth import admin_sidebar  # Absolute import
from census_app.helpers import send_agent_reminders, get_pending_holders_summary, status_badge, export_pending_holders_csv, export_pending_holders_pdf
import pandas as pd


def run():
    """
    Entry point for Admin Dashboard
    """
    # --- Page Config ---
    st.set_page_config(page_title="NACP - Admin Dashboard", layout="wide")

    # --- Sidebar ---
    admin_sidebar()

    # --- Session check ---
    if not st.session_state.get("logged_in") or st.session_state.get("user_role") != "Admin":
        st.warning("🔒 Please log in as an Admin to access this dashboard.")
        return

    st.title("👨‍💼 NACP - Admin Dashboard")
    st.success(f"✅ Welcome, {st.session_state.get('username')}!")

    # --- Send reminders automatically (once per session) ---
    if "reminders_sent" not in st.session_state:
        send_agent_reminders()
        st.session_state.reminders_sent = True
        st.info("📧 Agent reminders sent for pending holders.")

    # --- Admin Functions Section ---
    st.subheader("Admin Functions")
    st.write("Here you can manage users, assign agents, and monitor survey progress.")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕ Approve New Users"):
            st.info("Functionality to approve new users goes here.")

    with col2:
        if st.button("👷 Assign Agents to Farmers"):
            st.info("Functionality to assign agents goes here.")

    with col3:
        if st.button("📊 View Survey Reports"):
            st.info("Functionality to view survey reports goes here.")

    st.markdown("---")

    # --- Pending Holders Summary ---
    st.subheader("Pending Holder Registrations (24h review)")
    df_pending = get_pending_holders_summary()

    if not df_pending.empty:
        # Show table
        st.dataframe(df_pending)

        # Status badge column
        for idx, row in df_pending.iterrows():
            status_badge(row["Urgency"])

        # Export buttons
        col_export1, col_export2 = st.columns(2)
        with col_export1:
            if st.button("📁 Export CSV"):
                filename = export_pending_holders_csv(df_pending)
                st.success(f"CSV exported: {filename}")

        with col_export2:
            if st.button("📝 Export PDF"):
                filename = export_pending_holders_pdf(df_pending)
                st.success(f"PDF exported: {filename}")

    else:
        st.info("No pending holders at this time.")

    # --- Optional: Manual reminder trigger ---
    if st.button("🔄 Resend Agent Reminders"):
        send_agent_reminders()
        st.success("Agent reminders resent successfully.")
