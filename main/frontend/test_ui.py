import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st, uuid
from backend.ai.emotion_detection import (
    detect_mood, recommend, surprise_me, log_feedback_event, USER_MOODS_LOG, USER_FEEDBACK_LOG
)

import warnings
from sklearn.exceptions import InconsistentVersionWarning
warnings.filterwarnings("ignore", category=InconsistentVersionWarning)



import streamlit as st, uuid
from backend.ai.emotion_detection import (
    detect_mood, recommend, surprise_me, log_feedback_event, USER_MOODS_LOG, USER_FEEDBACK_LOG
)

st.set_page_config(page_title="Vyber AI Backend Testing Console", page_icon="🎬", layout="centered")
st.title("Vyber Backend Test Interface")

# Stable session id so logs group together
sid = st.session_state.setdefault("sid", str(uuid.uuid4()))

user_text = st.text_area(
    "How do you feel / what do you want?",
    "I want something light and funny"
)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Detect Mood"):
        m = detect_mood(user_text, session_id=sid)
        st.success(f"Detected mood: **{m}**")
        st.caption(f"Log file: {USER_MOODS_LOG}")

with col2:
    if st.button("Recommend"):
        m = detect_mood(user_text, session_id=sid)
        recs = recommend(m, top_n=6, user_text=user_text)
        st.subheader(f"Recommendations for mood: {m}")
        if not recs:
            st.warning("No recommendations available.")
        for r in recs:
            st.write(f"• **{r['title']}** | {r.get('genres')} | ⭐ {r.get('avg_rating', 0):.2f}")
            c1, c2 = st.columns(2)
            if c1.button(f"👍 Like: {r['title']}", key=f"like-{r['index']}"):
                log_feedback_event(sid, r["title"], m, "like")
                st.toast(f"Liked {r['title']}", icon="👍")
            if c2.button(f"⏭ Skip: {r['title']}", key=f"skip-{r['index']}"):
                log_feedback_event(sid, r["title"], m, "skip")
                st.toast(f"Skipped {r['title']}", icon="⏭")
        st.caption(f"Feedback log: {USER_FEEDBACK_LOG}")

with col3:
    if st.button("🎲 Surprise Me"):
        m = detect_mood(user_text, session_id=sid)
        s = surprise_me(m, user_text=user_text)
        if s:
            st.info(f"Surprise pick for **{m}**: **{s['title']}**")
        else:
            st.warning("No surprise available right now.")






          
