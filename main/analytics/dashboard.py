import streamlit as st
import pandas as pd
from pathlib import Path

LOG_FILE = Path(__file__).parent / "events.csv"

def show_dashboard():
    st.subheader("📊 Internal Analytics Dashboard")

    if not LOG_FILE.exists():
        st.warning("No events logged yet.")
        return

    df = pd.read_csv(LOG_FILE)

    if "event_type" not in df.columns:
        st.error("Invalid log format: 'event_type' column missing")
        return
    
    
    st.metric("Total Events", len(df))

    
    st.write("Event Distribution")
    st.bar_chart(df["event_type"].value_counts())