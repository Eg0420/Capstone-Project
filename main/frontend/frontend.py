import sys
from pathlib import Path
import os
from typing import Dict, Any
import base64
import uuid
import html
import streamlit as st
import pandas as pd
import re

CURRENT_FILE = Path(__file__).resolve()
MAIN_DIR = CURRENT_FILE.parents[1]
if str(MAIN_DIR) not in sys.path:
    sys.path.insert(0, str(MAIN_DIR))

from backend.ai.emotion_detection import load_movies, detect_mood, recommend, surprise_me
from analytics.logger import log_event
from analytics.dashboard import show_dashboard

# --- SESSION TRACKING ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

def is_gibberish(text: str) -> bool:
    t = (text or "").strip()
    if len(t) < 6:
        return True

    letters = sum(ch.isalpha() for ch in t)
    if letters / max(len(t), 1) < 0.6:
        return True

    if len(set(t.lower())) <= 2 and len(t) >= 8:
        return True

    if not re.search(r"[aeiouAEIOU]", t):
        return True

    if " " not in t and len(t) > 12:
        return True

    return False

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

        .vy-card {{
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 16px;
            padding: 14px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.35);
            transition: all 0.25s ease;

            min-height: 360px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;

        }}

        .vy-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 14px 40px rgba(0,0,0,0.55);
        }}

        .vy-expl {{
            display: -webkit-box;
            -webkit-line-clamp: 4;
            -webkit-box-orient: vertical;
            overflow: hidden;
            opacity: 0.95;
        }}

        .vy-title {{
            font-size: 28px;
                font-weight: 900;
                line-height: 1.15;
                margin: 2px 0 8px 0;
                color: #ffffff;
                text-shadow: 0 3px 16px rgba(0,0,0,0.55);
            }}

        .vy-title::after {{
                content: "";
                display: block;
                width: 56px;
                height: 4px;
                margin-top: 8px;
                border-radius: 999px;
                background: rgba(140, 70, 255, 0.75);
            }}

        .vy-genres {{
                font-size: 13px;
                opacity: 0.9;
                margin-bottom: 6px;
            }}

        .vy-rating {{
                font-size: 15px;
                margin-bottom: 10px;
            }}

        /* Buttons */
        div.stButton > button {{
            border-radius: 12px !important;
            padding: 0.65rem 0.9rem !important;
        }}

        div.stButton > button:hover {{
        background: rgba(140, 70, 255, 0.35) !important;
        border: 1px solid rgba(160, 100, 255, 0.65) !important;
        }}

        div.stButton > button:focus,
        div.stButton > button:active {{
            background: rgba(140, 70, 255, 0.45) !important;
            border: 1px solid rgba(160, 100, 255, 0.85) !important;
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

if "feedback" not in st.session_state:
    st.session_state.feedback = {}

if "mode_action" not in st.session_state:
    st.session_state.mode_action = None

if "clear_mood_text" not in st.session_state:
    st.session_state.clear_mood_text = False

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

# ==========================================================
# TABS
# ==========================================================
tabs = st.tabs(["🎬 Recommender", "📊 Analytics"])


# ==========================================================
# RECOMMENDER TAB
# ==========================================================
with tabs[0]:
    if st.session_state.clear_mood_text:
        if "mood_text" in st.session_state:
            del st.session_state["mood_text"]
        st.session_state.clear_mood_text = False
    # ---- ONE SINGLE GLASS PANEL WRAPPER ----
    st.subheader("1. Tell us your vibe")
    st.caption("Choose one option to set your mood. You can change it anytime.")

    mode = st.radio(
        "How would you like to set your mood?",
        options=["🧠 Type how you feel", "🎭 Choose my mood"],
        horizontal=True,
        index=None,
        key="mood_mode",
    )
    if mode is None:
        st.info("Select a mode above to continue.")
        st.stop()

    if "prev_mood_mode" not in st.session_state:
        st.session_state.prev_mood_mode = mode

    if mode != st.session_state.prev_mood_mode:
        st.session_state.mode_action = None
        st.session_state.prev_mood_mode = mode


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
        st.text_area(
            "Describe how you're feeling today (1–2 sentences)",
            placeholder="Example: I'm exhausted but I want something light and funny to relax with.",
            height=110,
            key="mood_text",
        )
        user_text = st.session_state.get("mood_text", "")

        if st.button("🔍 Detect my mood", use_container_width=True, key="btn_detect_mood"):
            if not user_text.strip():
                st.warning("Please type something first.")
                st.stop()

            if is_gibberish(user_text):
                st.error("That looks like random text. Please type a real sentence (e.g., 'I feel tired and want something funny').")
                log_event("invalid_text_input", {"reason": "gibberish", "session_id": st.session_state.session_id})
                st.stop()

            with st.spinner("Analyzing your text..."):
                try:
                    detected = detect_mood(user_text)
                    detected = (detected or "").strip().lower()

                    st.session_state.chosen_mood_code = detected
                    st.session_state.mode_action = None
                    st.session_state.feedback = {}
                    log_event("mood_detected", {"mood": detected, "session_id": st.session_state.session_id})
                    log_event("mood_selected", {"mood": detected, "source": "text_detect", "session_id": st.session_state.session_id})
                    st.success(f"Detected mood: **{mood_code_to_label(detected)}**")
                    st.rerun()

                except Exception as e:
                    st.error(f"Could not detect mood: {e}")

    elif mode == "🎭 Choose my mood":
        st.markdown("### Select your current mood")
        mood_cols = st.columns(6)
        for i, mood_code in enumerate(MOOD_ORDER):
            with mood_cols[i]:
                if st.button(MOOD_LABELS[mood_code], use_container_width=True, key=f"mood_btn_{mood_code}"):
                    st.session_state.chosen_mood_code = mood_code
                    st.session_state.mode_action = None
                    st.session_state.feedback = {}
                    st.session_state.clear_mood_text = True                    
                    log_event("mood_selected", {"mood": mood_code, "source": "manual_select", "session_id": st.session_state.session_id})
                    st.rerun()

    st.markdown("")

    # ---- Controls row ----
    c1, c2, c3, c4 = st.columns([1.2, 1, 1, 0.7])
    with c1:
        top_n = st.slider("Results", 3, 15, 6, key="slider_results", label_visibility="visible")

    with c2:
        if st.button("✨ Recommend", use_container_width=True, key="btn_recommend"):
            st.session_state.mode_action = "recommend"
            st.session_state.feedback = {}
            st.rerun()

    with c3:
        if st.button("🎲 Surprise", use_container_width=True, key="btn_surprise"):
            st.session_state.mode_action = "surprise"
            st.rerun()

    with c4:
        reset_btn = st.button("↩ Reset", use_container_width=True, key="btn_reset")
        if reset_btn:
            st.session_state.chosen_mood_code = None
            st.session_state.mode_action = None
            st.session_state.feedback = {}
            st.session_state.clear_mood_text = True
            log_event("mood_reset", {"session_id": st.session_state.session_id})
            st.rerun()

    # ---- Movie tile renderer ----
    def render_movie_tile(movie: Dict[str, Any], idx: int):
        title = movie.get("title", "Unknown title")
        genres = " • ".join(movie.get("genres", [])[:3]) if movie.get("genres") else ""
        rating = movie.get("avg_rating", None)
        expl = html.escape(movie.get("explanation", "") or "")

        existing = st.session_state.feedback.get(title)

        rating_html = f"<div class='vy-rating'>⭐ {float(rating):.1f}/5</div>" if rating is not None else ""
        genres_html = f"<div class='vy-genres'>{html.escape(genres)}</div>" if genres else ""

        st.markdown(
            f"""
            <div class="vy-card">
                <div class="vy-title">{html.escape(title)}</div>
                {genres_html}
                {rating_html}
                <div class="vy-expl">{expl}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Buttons row
        c_like, c_dislike = st.columns(2)
        like_label = "👍 Like" if existing != "like" else "✅ Liked"
        dislike_label = "👎 Dislike" if existing != "dislike" else "✅ Disliked"

        with c_like:
            if st.button(like_label, use_container_width=True, key=f"like_{idx}", disabled=(existing is not None)):
                st.session_state.feedback[title] = "like"
                log_event("feedback_given", {
                    "movie": title,
                    "action": "like",
                    "session_id": st.session_state.session_id
                })
                st.toast("Saved: Like ✅")
                st.rerun()

        with c_dislike:
            if st.button(dislike_label, use_container_width=True, key=f"dislike_{idx}", disabled=(existing is not None)):
                st.session_state.feedback[title] = "dislike"
                log_event("feedback_given", {
                    "movie": title,
                    "action": "dislike",
                    "session_id": st.session_state.session_id
                })
                st.toast("Saved: Dislike ✅")
                st.rerun()

    # ---- Recommend ----
    if st.session_state.mode_action == "recommend":
        mood = st.session_state.chosen_mood_code
        if not mood:
            st.warning("Please select a mood first (detect or choose).")
            st.stop()
        typed_text = st.session_state.get("mood_text", "")

        log_event("recommendation_requested", {
            "mood": mood,
            "top_n": top_n,
            "session_id": st.session_state.session_id
        })

        st.subheader("2. Your recommendations")
        st.caption(f"Using mood: {mood}")

        with st.spinner("Finding best matches..."):
            movies = recommend(
                mood=mood,
                top_n=top_n,
                user_text=typed_text,
            )

        log_event("recommendation_shown", {
            "mood": mood,
            "count": len(movies) if movies else 0,
            "session_id": st.session_state.session_id
        })

        if not movies:
            st.warning("No recommendations returned.")
        else:
            cols = st.columns(3)
            for i, m in enumerate(movies):
                with cols[i % 3]:
                    render_movie_tile(m, idx=i)

    # ---- Surprise ----
    if st.session_state.mode_action == "surprise":
        mood = st.session_state.chosen_mood_code
        if not mood:
            st.warning("Please select a mood first.")
            st.stop()
        typed_text = st.session_state.get("mood_text", "")

        log_event("surprise_clicked", {
            "mood": mood,
            "session_id": st.session_state.session_id
        })

        st.subheader("🎲 Surprise pick")

        with st.spinner("Picking a surprise..."):
            movie = surprise_me(
                mood=mood,
                user_text=typed_text,
            )

        log_event("surprise_shown", {
            "mood": mood,
            "movie": movie.get("title", "Unknown title") if isinstance(movie, dict) else "Unknown title",
            "session_id": st.session_state.session_id
        })

        render_movie_tile(movie, idx=999999)


# ==========================================================
# ANALYTICS TAB
# ==========================================================
with tabs[1]:
    show_dashboard()