import sys
from pathlib import Path
import os

CURRENT_FILE = Path(__file__).resolve()
MAIN_DIR = CURRENT_FILE.parents[1]
if str(MAIN_DIR) not in sys.path:
    sys.path.insert(0, str(MAIN_DIR))

from backend.ai.emotion_detection import load_movies, detect_mood, recommend, surprise_me
from analytics.logger import log_event
from analytics.dashboard import show_dashboard
from typing import List, Dict, Any
import streamlit as st
import pandas as pd
import base64
from pathlib import Path


def set_background(image_name: str):
    """
    Set a blurred movie-poster collage as the app background,
    with a dark overlay for accessibility (good contrast).
    """
    bg_path = Path(__file__).parent / "bg_vyber.jpg"

    if not bg_path.exists():
        # Fail gracefully if the image is missing
        return

    with open(bg_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
# ---------- BG CSS ----------
    st.markdown(
        f"""
        <style>
        /* Page background */
        .stApp {{
            background-image: linear-gradient(
                rgba(0, 0, 0, 0.70),
                rgba(0, 0, 0, 0.70)
            ), url("data:image/jpg;base64,{encoded_string}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
        }}

        /* Main block container – keep it slightly transparent but solid enough for text */
        .block-container {{
            background-color: rgba(0, 0, 0, 0.35);
            border-radius: 14px;
            padding: 1.2rem 2rem;
        }}

        /* Ensure default text is high-contrast */
        h1, h2, h3, h4, h5, h6, p, span, label {{
            color: #f5f5f5 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
# ---------- Header CSS ----------
st.markdown("""
<style>
.header-container {
    display: flex;
    align-items: center;
    gap: 20px;  /* spacing between logo and text */
    margin-bottom: 20px;
}

.header-logo img {
    width: 140px;
}

.header-title {
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.header-title h1 {
    margin: 0;
    padding: 0;
    font-size: 38px;
    font-weight: bold;
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)


# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Vyber – Movies that match your vibe",
    page_icon="🎬",
    layout="wide"
)
set_background("bg_vyber.jpg")

# ---------- LOAD DATA (for stats / debug only) ----------
@st.cache_data
def get_movies_df() -> pd.DataFrame:
    """
    Get the full movies dataframe from the recommender utilities.
    The utility internally loads loaded_movies_df.csv + ratings etc.
    """
    try:
        return load_movies()
    except Exception as e:
        st.error(f"Failed to load movies from utils: {e}")
        return pd.DataFrame()


MOVIES_DF = get_movies_df()

# ---------- SESSION STATE ----------
if "chosen_mood_code" not in st.session_state:
    st.session_state.chosen_mood_code = None

if "user_text" not in st.session_state:
    st.session_state.user_text = ""

# ---------- MOOD LABELS FOR UI ----------
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


def mood_label_to_code(label: str) -> str:
    for code, txt in MOOD_LABELS.items():
        if txt == label:
            return code
    # fallback: strip emoji if user somehow passes raw label
    return label.split()[-1].lower()


# ---------- LOGO + HEADER ----------
logo_path = os.path.join(MAIN_DIR, "frontend", "vyber main final transparent.png")
logo_col, title_col = st.columns([1, 2])

with logo_col:
    if os.path.exists(logo_path):
        st.image(logo_path, width=350)
    else:
        st.markdown("### 🎬 Vyber")

with title_col:
    st.markdown(
        """
        <div class="header-container">
        <h1> Vyber - Movies that match your vibe </h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- TABS ----------
tabs = st.tabs(["🎬 Recommender", "📊 Analytics"])

# ---------- RECOMMENDER TAB ----------
with tabs[0]:
    top_n = st.slider("Number of recommendations", min_value=3, max_value=15, value=6)

    st.subheader("1. Tell us your vibe")

    mode = st.radio(
        "How would you like to set your mood?",
        options=["🧠 Type how you feel", "🎭 Choose my mood"],
        horizontal=True,
        index=None
    )

    # local inputs (session_state holds the "remembered" values)
    user_text = ""

    if mode == "🧠 Type how you feel":
        user_text = st.text_area(
            "Describe how you're feeling today (1–2 sentences)",
            placeholder="Example: I'm exhausted but I want something light and funny to relax with.",
            height=120,
        )

        detect_btn = st.button("🔍 Detect my mood")
        if detect_btn and user_text.strip():
            with st.spinner("Analyzing your text and detecting mood..."):
                try:
                    detected_mood_code = detect_mood(user_text)
                    log_event("mood_detected", {"mood": detected_mood_code})

                    st.success(f"Detected mood: **{mood_code_to_label(detected_mood_code)}**")

                    st.session_state.chosen_mood_code = (detected_mood_code or "").strip().lower()
                    st.session_state.user_text = user_text
                except Exception as e:
                    st.error(f"Could not detect mood: {e}")

    elif mode == "🎭 Choose my mood":
        st.markdown("#### Select your current mood")
        mood_label = st.radio(
            " ",
            options=[MOOD_LABELS[m] for m in MOOD_ORDER],
            horizontal=True,
        )

        chosen_mood_code = mood_label_to_code(mood_label)

        st.session_state.chosen_mood_code = (chosen_mood_code or "").strip().lower()
        st.session_state.user_text = ""

    st.markdown("---")

    # ---------- ACTION BUTTONS ----------
    col_rec, col_surprise = st.columns([2, 1])
    with col_rec:
        rec_btn = st.button("✨ Get recommendations", use_container_width=True)
    with col_surprise:
        surprise_btn = st.button("🎲 Surprise me", use_container_width=True)

    # ---------- MOVIE CARD RENDERER ----------
    def render_movie_card(movie: Dict[str, Any], rank: int):
        title = movie.get("title", "Unknown title")
        genres = movie.get("genres", [])
        avg_rating = movie.get("avg_rating", None)
        vibe_cluster = movie.get("vibe_cluster", None)
        explanation = movie.get("explanation", "")

        badges = []
        if isinstance(genres, (list, tuple)):
            badges.append(" | ".join(genres[:3]))
        if avg_rating is not None:
            badges.append(f"⭐ {avg_rating:.1f}/5")
        if vibe_cluster is not None:
            badges.append(f"Vibe cluster #{vibe_cluster}")

        badge_text = " • ".join(badges)

        with st.container():
            st.markdown(
                f"### #{rank} – {title}\n"
                f"<span style='color:#ffaa00;'>{badge_text}</span>",
                unsafe_allow_html=True,
            )
            st.write(explanation)
            st.markdown("---")

    # ---------- RECOMMENDATIONS ----------
    if rec_btn:
        mood_to_use = st.session_state.chosen_mood_code
        text_to_use = st.session_state.user_text

        if not mood_to_use:
            st.warning("Please choose a mood first (type + detect OR choose manually).")
            st.stop()

        log_event("recommendation_requested", {"mood": mood_to_use, "top_n": top_n})
        st.subheader("2. Your recommendations")
        st.caption(f"Using mood: {mood_to_use}")

        with st.spinner("Matching your mood to movies..."):
            try:
                raw_recs: List[Dict[str, Any]] = recommend(
                    mood=mood_to_use,
                    top_n=top_n,
                    user_text=text_to_use if isinstance(text_to_use, str) else None,
                )

                if not raw_recs:
                    st.warning("No recommendations were returned. Try a different mood or check the backend.")
                else:
                    for i, m in enumerate(raw_recs, start=1):
                        render_movie_card(m, rank=i)

            except Exception as e:
                st.error(f"Recommendation failed: {e}")

    # ---------- SURPRISE ME ----------
    if surprise_btn:
        mood_to_use = st.session_state.chosen_mood_code
        text_to_use = st.session_state.user_text

        if not mood_to_use:
            st.warning("Please choose a mood first.")
            st.stop()

        log_event("surprise_clicked", {"mood": mood_to_use})
        st.subheader("🎲 Surprise pick")

        with st.spinner("Picking something a little different but still on-vibe..."):
            try:
                surprise_movie = surprise_me(
                    mood=mood_to_use,
                    user_text=text_to_use if isinstance(text_to_use, str) else None,
                )
                render_movie_card(surprise_movie, rank=1)
            except Exception as e:
                st.error(f"Surprise-me failed: {e}")


# ---------- ANALYTICS TAB ----------
with tabs[1]:
    show_dashboard()