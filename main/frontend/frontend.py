import sys
from pathlib import Path
import os
from typing import List, Dict, Any
import base64

import streamlit as st
import pandas as pd

CURRENT_FILE = Path(__file__).resolve()
MAIN_DIR = CURRENT_FILE.parents[1]
if str(MAIN_DIR) not in sys.path:
    sys.path.insert(0, str(MAIN_DIR))

from backend.ai.emotion_detection import load_movies, detect_mood, recommend, surprise_me
from analytics.logger import log_event
from analytics.dashboard import show_dashboard


# ==========================================================
# BACKGROUND + GLOBAL UI STYLING
# ==========================================================
def img_to_base64(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return base64.b64encode(p.read_bytes()).decode("utf-8")


def set_background():
    bg_path = Path(__file__).parent / "bg_vyber.jpg"
    bg_b64 = img_to_base64(str(bg_path)) if bg_path.exists() else ""

    st.markdown(
        f"""
        <style>
        /* App background */
        .stApp {{
            background-image: linear-gradient(
                rgba(0, 0, 0, 0.72),
                rgba(0, 0, 0, 0.72)
            ), url("data:image/jpg;base64,{bg_b64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
        }}

        /* Remove default white sheet */
        .block-container {{
            background: transparent !important;
            padding-top: 0.8rem !important;
            padding-bottom: 2rem !important;
        }}

        h1,h2,h3,h4,h5,h6,p,span,label {{
            color: #f5f5f5 !important;
        }}

        /* ---------- FIX: Remove weird empty rounded bar & extra spacing from tabs ---------- */
        hr {{ display: none !important; }}

        div[data-testid="stTabs"] {{
            margin-top: -10px;
        }}

        div[data-testid="stTabs"] > div {{
            background: transparent !important;
            box-shadow: none !important;
            border: none !important;
        }}

        div[data-testid="stTabs"] div[role="tabpanel"] {{
            padding-top: 0.25rem !important;
        }}

        /* ---------- Glass panel wrapper ---------- */
        .vy-panel {{
            max-width: 1050px;
            margin: 0 auto 20px auto;
            padding: 20px 20px 16px 20px;
            border-radius: 18px;
            background: rgba(0,0,0,0.42);
            border: 1px solid rgba(255,255,255,0.14);
            box-shadow: 0 18px 46px rgba(0,0,0,0.45);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
        }}

        /* Chips */
        .vy-chip {{
            display:inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.15);
            font-size: 13px;
            margin: 6px 0 8px 0;
        }}

        .vy-muted {{
            opacity: 0.85;
            font-size: 13px;
        }}

        /* Movie card */
        .vy-card {{
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 16px;
            padding: 14px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.35);
            transition: all 0.25s ease;
        }}

        .vy-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 14px 40px rgba(0,0,0,0.55);
        }}

        /* Buttons */
        div.stButton > button {{
            border-radius: 12px !important;
            padding: 0.65rem 0.9rem !important;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="Vyber – Movies that match your vibe",
    page_icon="🎬",
    layout="wide"
)
set_background()


# ==========================================================
# SESSION STATE
# ==========================================================
if "chosen_mood_code" not in st.session_state:
    st.session_state.chosen_mood_code = None

if "user_text" not in st.session_state:
    st.session_state.user_text = ""


# ==========================================================
# MOODS
# ==========================================================
MOOD_LABELS = {
    "happy": "😄 Happy",
    "sad": "😢 Sad",
    "romantic": "🥰 Romantic",
    "action": "🔥 Action",
    "scary": "👻 Scary",
    "fantasy": "✨ Fantasy",
}
MOOD_ORDER = ["happy", "sad", "romantic", "action", "scary", "fantasy"]


def mood_code_to_label(mood: str) -> str:
    mood = (mood or "").lower()
    return MOOD_LABELS.get(mood, mood.capitalize())


# ==========================================================
# HEADER (Centered logo + title)
# ==========================================================
logo_path = os.path.join(MAIN_DIR, "frontend", "vyber main final transparent.png")
logo_b64 = img_to_base64(logo_path)

st.markdown(
    f"""
    <div style="text-align:center; padding: 6px 0 10px 0;">
      <div style="display:inline-flex; align-items:center; gap:16px;">
        {"<img src='data:image/png;base64," + logo_b64 + "' style='height:54px; width:auto;' />" if logo_b64 else ""}
        <span style="font-size:54px; font-weight:800; color:#ffffff;">Vyber</span>
      </div>
      <div style="margin-top:6px; font-size:18px; opacity:0.85; color:#ffffff;">
        Movies that match your vibe — in seconds.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# (No st.markdown("---") here — it created extra bar/space)


# ==========================================================
# TABS
# ==========================================================
tabs = st.tabs(["🎬 Recommender", "📊 Analytics"])


# ==========================================================
# RECOMMENDER TAB
# ==========================================================
with tabs[0]:

    # ---- ONE SINGLE GLASS PANEL WRAPPER ----
    st.markdown('<div class="vy-panel">', unsafe_allow_html=True)

    st.subheader("1. Tell us your vibe")
    st.caption("Choose one option to set your mood. You can change it anytime.")

    mode = st.radio(
        "How would you like to set your mood?",
        options=["🧠 Type how you feel", "🎭 Choose my mood"],
        horizontal=True,
        index=None,
    )

    # Show current mood chip
    if st.session_state.chosen_mood_code:
        st.markdown(
            f"<div class='vy-chip'>Current mood: {mood_code_to_label(st.session_state.chosen_mood_code)}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<div class='vy-muted'>No mood selected yet.</div>", unsafe_allow_html=True)

    # ---- Mode UI ----
    if mode == "🧠 Type how you feel":
        user_text = st.text_area(
            "Describe how you're feeling today (1–2 sentences)",
            placeholder="Example: I'm exhausted but I want something light and funny to relax with.",
            height=110,
        )

        if st.button("🔍 Detect my mood", use_container_width=True):
            if user_text.strip():
                with st.spinner("Analyzing your text..."):
                    try:
                        detected = detect_mood(user_text)
                        log_event("mood_selected", {"mood": mood})
                        log_event("mood_detected", {"mood": detected})
                        st.success(f"Detected mood: **{mood_code_to_label(detected)}**")
                        st.session_state.chosen_mood_code = (detected or "").strip().lower()
                        st.session_state.user_text = user_text
                    except Exception as e:
                        st.error(f"Could not detect mood: {e}")
            else:
                st.warning("Please type something first.")

    elif mode == "🎭 Choose my mood":
        st.markdown("### Select your current mood")
        mood_cols = st.columns(6)
        for i, mood_code in enumerate(MOOD_ORDER):
            with mood_cols[i]:
                if st.button(MOOD_LABELS[mood_code], use_container_width=True):
                    st.session_state.chosen_mood_code = mood_code
                    st.session_state.user_text = ""

    st.markdown("")

    # ---- Controls row inside the SAME container ----
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        top_n = st.slider("Results", 3, 15, 6)
    with c2:
        rec_btn = st.button("✨ Recommend", use_container_width=True)
    with c3:
        surprise_btn = st.button("🎲 Surprise", use_container_width=True)

    if st.button("↩ Reset mood", use_container_width=True):
        st.session_state.chosen_mood_code = None
        st.session_state.user_text = ""

    st.markdown("</div>", unsafe_allow_html=True)  # end wrapper

    st.markdown("")  # small space after wrapper


    # ---- Movie tile renderer ----
    def render_movie_tile(movie: Dict[str, Any]):
        st.markdown('<div class="vy-card">', unsafe_allow_html=True)
        st.markdown(f"### {movie.get('title', 'Unknown title')}")
        if movie.get("genres"):
            st.caption(" • ".join(movie["genres"][:3]))
        if movie.get("avg_rating") is not None:
            st.markdown(f"⭐ {float(movie['avg_rating']):.1f}/5")
        st.write(movie.get("explanation", ""))
        st.markdown("</div>", unsafe_allow_html=True)


    # ---- Recommend ----
    if rec_btn:
        mood = st.session_state.chosen_mood_code
        if not mood:
            st.warning("Please select a mood first (detect or choose).")
            st.stop()

        log_event("recommendation_requested", {"mood": mood, "top_n": top_n})
        log_event("recommendation_shown", {"mood": mood, "count": len(recommendations)})

        st.subheader("2. Your recommendations")
        st.caption(f"Using mood: {mood}")

        with st.spinner("Finding best matches..."):
            movies = recommend(
                mood=mood,
                top_n=top_n,
                user_text=st.session_state.user_text,
            )

        if not movies:
            st.warning("No recommendations returned.")
        else:
            cols = st.columns(3)
            for i, m in enumerate(movies):
                with cols[i % 3]:
                    render_movie_tile(m)


    # ---- Surprise ----
    if surprise_btn:
        mood = st.session_state.chosen_mood_code
        if not mood:
            st.warning("Please select a mood first.")
            st.stop()

        log_event("surprise_clicked", {"mood": mood})

        st.subheader("🎲 Surprise pick")

        with st.spinner("Picking a surprise..."):
            movie = surprise_me(
                mood=mood,
                user_text=st.session_state.user_text,
            )

        render_movie_tile(movie)


# ==========================================================
# ANALYTICS TAB
# ==========================================================
with tabs[1]:
    show_dashboard()