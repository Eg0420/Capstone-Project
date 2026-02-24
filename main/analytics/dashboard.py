import os
import streamlit as st
import pandas as pd
from pathlib import Path

LOG_FILE = Path(__file__).parent / "events.csv"

def show_dashboard():
    st.subheader("📊 Internal Analytics Dashboard")

    if not LOG_FILE.exists():
        st.info("No events logged yet.")
        return

    try:
        if LOG_FILE.stat().st_size == 0:
            st.info("No analytics events yet. Use Detect Mood / Get Recommendations first.")
            return
    except Exception:
        st.info("Analytics log file cannot be accessed right now.")
        return

    try:
        df = pd.read_csv(LOG_FILE)
    except pd.errors.EmptyDataError:
        st.info("No analytics data available yet.")
        return
    except Exception as e:
        st.error(f"Error reading analytics file: {e}")
        return

    if df.empty:
        st.info("No events logged yet.")
        return

    if "event_type" not in df.columns:
        st.error("Invalid log format: 'event_type' column missing")
        st.write("Columns found:", list(df.columns))
        return

    st.metric("Total Events", len(df))
    
    st.write("Event Distribution")
    st.bar_chart(df["event_type"].value_counts())