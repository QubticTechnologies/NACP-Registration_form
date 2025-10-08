import streamlit as st
import pandas as pd
from sqlalchemy import text
from census_app.db import engine

def holder_dashboard(holder_id):
    """
    Displays the Holder Dashboard for the given holder_id,
    showing holder details, farms, and location map.
    """
    st.header(f"Holder Dashboard - ID: {holder_id}")

    try:
        # --- Holder Details ---
        with engine.connect() as conn:
            holder_info = conn.execute(
                text("SELECT * FROM holders WHERE holder_id=:hid"),
                {"hid": holder_id}
            ).fetchone()

        if holder_info:
            st.subheader("Holder Details")
            st.write(holder_info)
        else:
            st.warning("No holder information found.")

        # --- Farms / Holdings ---
        with engine.connect() as conn:
            holdings = conn.execute(
                text("""SELECT name, latitude, longitude
                        FROM holders
                        WHERE holder_id=:hid
                        AND latitude IS NOT NULL AND longitude IS NOT NULL"""),
                {"hid": holder_id}
            ).fetchall()

        if holdings:
            df_map = pd.DataFrame(holdings, columns=["Name", "Latitude", "Longitude"])
        else:
            df_map = pd.DataFrame([[None, 25.0343, -77.3963]], columns=["Name", "Latitude", "Longitude"])

        # --- Show map with holder locations ---
        st.subheader("Farm Location Map")
        df_map_renamed = df_map.rename(columns={"Latitude": "lat", "Longitude": "lon"})
        st.map(df_map_renamed[["lat", "lon"]], zoom=7)

        if not holdings:
            st.info("No farm locations found. Showing default map location.")

        # --- Optional: Show farms table ---
        st.subheader("Farms / Holdings Table")
        st.table(df_map)

    except Exception as e:
        st.error(f"Error loading holder dashboard: {e}")
