"""
Emotion detection and movie recommendation utilities for Vyber.

This module exposes helpers for the backend & frontend:

- load_movies() → returns the movies DataFrame
- detect_mood(text) → maps free-text input to one of our coarse moods
- recommend(mood, ...) → returns a list of recommended movies
- surprise_me(mood, ...) → returns one "surprise" movie using vibe clusters
- log_mood_event(...) → logs detected moods to CSV
- log_feedback_event(...) → logs like/skip/save feedback to CSV
"""

import os
import ast
import csv
import random
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
import joblib

# HuggingFace pipeline is optional (safe fallback)
# ---------------------------
# Emotion pipeline (optional) and helper
# ---------------------------
try:
    from transformers import pipeline
    # Use return_all_scores=True so we can always pick the top label safely
    emotion_pipeline = pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        return_all_scores=True
    )
except Exception:
    emotion_pipeline = None

# Map HF labels to coarse moods (you already defined emotion_to_mood_map above — keep it)
# emotion_to_mood_map = {
#     "joy": "happy", "love": "happy", "optimism": "happy",
#     "anger": "angry", "sadness": "sad", "fear": "fear",
#     "surprise": "surprise", "neutral": "neutral",
#     "disgust": "neutral",  # optional mapping if you keep 'disgust'
# }

def _extract_top_dict(results):
    """
    Normalize HF pipeline outputs:
    - results can be list[dict] or list[list[dict]]
    Return the dict with the max 'score', or None.
    """
    try:
        if not results:
            return None
        # Case A: [[{label, score}, ...]]
        if isinstance(results, list) and results and isinstance(results[0], list):
            candidates = results[0]
        # Case B: [{label, score}, ...]
        elif isinstance(results, list) and results and isinstance(results[0], dict):
            candidates = results
        else:
            return None
        return max(candidates, key=lambda d: d.get("score", 0.0))
    except Exception:
        return None


# -------------------------------------------------------------------
# Paths for models and data (Harsha)
# -------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR   = os.path.join(BASE_DIR, "data")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

TFIDF_VECTORIZER_PATH = os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl")
COSINE_SIM_MATRIX_PATH = os.path.join(MODELS_DIR, "cosine_sim_matrix.npy")
MOVIES_DF_PATH = os.path.join(MODELS_DIR, "loaded_movies_df.csv")
KMEANS_MODEL_PATH = os.path.join(MODELS_DIR, "kmeans_vibe_model.pkl")

# CSV logs
USER_MOODS_LOG    = os.path.join(DATA_DIR, "user_moods.csv")
USER_FEEDBACK_LOG = os.path.join(DATA_DIR, "user_feedback.csv")


# -------------------------------------------------------------------
# Load model artifacts (safe fallback version)
# -------------------------------------------------------------------

# 1) TF-IDF vectorizer
try:
    tfidf_vectorizer = joblib.load(TFIDF_VECTORIZER_PATH)
except Exception:
    tfidf_vectorizer = None

# 2) Movie dataframe (required)
if not os.path.exists(MOVIES_DF_PATH):
    raise FileNotFoundError(f"[ERROR] Movies dataframe not found at {MOVIES_DF_PATH}")

movies_df = pd.read_csv(MOVIES_DF_PATH)

# 3) Cosine similarity matrix
try:
    cosine_sim_matrix = np.load(COSINE_SIM_MATRIX_PATH)
except Exception:
    n = len(movies_df)
    cosine_sim_matrix = np.eye(n, dtype=float)  # fallback identity

# 4) KMeans model (optional)
try:
    kmeans_model = joblib.load(KMEANS_MODEL_PATH)
except Exception:
    kmeans_model = None


# -------------------------------------------------------------------
# Data cleaning helpers (Harsha)
# -------------------------------------------------------------------

def _ensure_genres_list(val):
    """Ensure genres column is a Python list."""
    if isinstance(val, list):
        return val
    if isinstance(val, str) and val.startswith("[") and "]" in val:
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
    if isinstance(val, str):
        return val.split("|")
    return []

if "genres_list" in movies_df.columns:
    movies_df["genres_list"] = movies_df["genres_list"].apply(_ensure_genres_list)
elif "genres" in movies_df.columns:
    movies_df["genres_list"] = movies_df["genres"].apply(_ensure_genres_list)

if "vibe_cluster" not in movies_df.columns:
    movies_df["vibe_cluster"] = -1
else:
    movies_df["vibe_cluster"] = movies_df["vibe_cluster"].fillna(-1).astype(int)


# -------------------------------------------------------------------
# Core functions exposed to frontend
# -------------------------------------------------------------------

def load_movies():
    """Return a copy of the loaded movies dataframe."""
    return movies_df.copy()

DEFAULT_MOOD = "neutral"

# If you already defined emotion_to_mood_map above, we will reuse it.
# If not, uncomment this map:
# emotion_to_mood_map = {
#     "joy": "happy", "love": "happy", "optimism": "happy",
#     "anger": "angry", "sadness": "sad", "fear": "fear",
#     "surprise": "surprise", "neutral": "neutral",
#     "disgust": "neutral",
# }

# ---------------------------
# Logging helpers (Harsha)
# ---------------------------

def _append_csv_row(path: str, header: list, row: list) -> None:
    file_exists = os.path.exists(path)
    with open(path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow(row)

def log_mood_event(
    session_id: str,
    source: str,
    mood: str,
    raw_text: Optional[str] = None,
    detected_label: Optional[str] = None,
    score: Optional[float] = None,
) -> None:
    ts = datetime.utcnow().isoformat()
    _append_csv_row(
        USER_MOODS_LOG,
        header=["timestamp_utc", "session_id", "source", "mood", "raw_text", "detected_label", "score"],
        row=[ts, session_id, source, mood, raw_text or "", detected_label or "", score if score is not None else ""],
    )

def log_feedback_event(session_id: str, movie_title: str, mood: str, action: str) -> None:
    ts = datetime.utcnow().isoformat()
    _append_csv_row(
        USER_FEEDBACK_LOG,
        header=["timestamp_utc", "session_id", "movie_title", "mood", "action"],
        row=[ts, session_id, movie_title, mood, action],
    )

# ---------------------------
# Mood detection
# ---------------------------

def detect_mood(text: str, session_id: Optional[str] = None) -> str:
    """
    Detect a coarse mood from free text.
    Uses HF pipeline if available; otherwise falls back to a simple heuristic.
    If session_id is provided, logs the event.
    """
    if not isinstance(text, str) or not text.strip():
        mood = DEFAULT_MOOD
        if session_id:
            log_mood_event(session_id, "ai_detected", mood, raw_text=text)
        return mood

    # Try HF pipeline first
    if 'emotion_pipeline' in globals() and emotion_pipeline is not None:
        try:
            results = emotion_pipeline(text)
            # _extract_top_dict must exist above – we provided a fixed version earlier
            top = _extract_top_dict(results)
            if top:
                label = str(top.get("label", "")).lower()
                score = float(top.get("score", 0.0))
                mood = emotion_to_mood_map.get(label, DEFAULT_MOOD)
                if session_id:
                    log_mood_event(session_id, "ai_detected", mood, raw_text=text, detected_label=label, score=score)
                return mood
        except Exception:
            pass

    # Heuristic fallback
    lowered = text.lower()
    if any(w in lowered for w in ["happy", "glad", "joy", "awesome", "good", "great", "love", "excited"]):
        mood = "happy"
    elif any(w in lowered for w in ["sad", "unhappy", "depress", "lonely", "down"]):
        mood = "sad"
    elif any(w in lowered for w in ["angry", "mad", "furious", "annoyed"]):
        mood = "angry"
    elif any(w in lowered for w in ["scared", "afraid", "fear", "terrified"]):
        mood = "fear"
    elif any(w in lowered for w in ["surprise", "shocked", "wow", "amazed"]):
        mood = "surprise"
    elif any(w in lowered for w in ["calm", "relaxed", "chill"]):
        mood = "calm"
    else:
        mood = DEFAULT_MOOD

    if session_id:
        log_mood_event(session_id, "ai_detected", mood, raw_text=text)
    return mood

# ---------------------------
# Recommendation
# ---------------------------

def _row_to_public(idx: int) -> dict:
    row = movies_df.iloc[idx]
    return {
        "index": int(idx),
        "title": row.get("title", ""),
        "genres": row.get("genres_list", row.get("genres", [])),
        "avg_rating": float(row.get("avg_rating", 0.0)),
        "vibe_cluster": int(row.get("vibe_cluster", -1)),
    }

def recommend(mood: str, top_n: int = 10, user_text: Optional[str] = None) -> list[dict]:
    """
    Rank movies using:
      - cosine_sim_matrix row sums (popularity/centrality proxy),
      - avg_rating,
      - simple mood->genre boosts.
    Works even if cosine matrix is identity (fallback).
    """
    n = len(movies_df)
    scores = np.zeros(n, dtype=float)

    # 1) cosine popularity proxy
    try:
        sim_sums = np.nan_to_num(cosine_sim_matrix.sum(axis=1))
        if sim_sums.shape[0] == n:
            scores += sim_sums
    except Exception:
        pass

    # 2) avg_rating boost
    try:
        ratings = movies_df["avg_rating"].fillna(movies_df["avg_rating"].mean()).to_numpy()
        scores += (ratings - ratings.mean()) * 0.5
    except Exception:
        pass

    # 3) mood-genre boost
    mood_genres = {
        "happy": ["comedy", "romance", "family"],
        "sad": ["drama", "romance"],
        "angry": ["action", "thriller"],
        "fear": ["horror", "thriller"],
        "surprise": ["mystery", "sci-fi", "fantasy"],
        "calm": ["documentary", "drama"],
        "excited": ["action", "adventure"],
        "neutral": [],
    }
    boosts = set([g.lower() for g in mood_genres.get(mood, [])])
    if boosts:
        for i in range(n):
            gs = movies_df.iloc[i].get("genres_list", movies_df.iloc[i].get("genres", []))
            gs_norm = " ".join([str(x).lower() for x in (gs if isinstance(gs, list) else [gs])])
            if any(b in gs_norm for b in boosts):
                scores[i] += 1.0

    # sort and build output
    order = np.argsort(-scores)
    out = []
    seen = set()
    for idx in order:
        if len(out) >= int(top_n):
            break
        item = _row_to_public(int(idx))
        t = item["title"]
        if t and t not in seen:
            seen.add(t)
            out.append(item)
    return out

# ---------------------------
# Surprise Me
# ---------------------------

def surprise_me(mood: str, user_text: Optional[str] = None) -> dict | None:
    """
    Return one movie from a *different* vibe cluster than the dominant
    cluster in the main recommendations. Falls back gracefully.
    """
    recs = recommend(mood, top_n=30, user_text=user_text)
    if not recs:
        # fallback to a mid-rated movie
        row = movies_df.sort_values("avg_rating").iloc[len(movies_df) // 2]
        return _row_to_public(int(row.name))

    # find most common cluster in recs
    counts = {}
    for r in recs:
        c = int(r.get("vibe_cluster", -1))
        counts[c] = counts.get(c, 0) + 1
    dominant = max(counts.items(), key=lambda kv: kv[1])[0]

    # pick from different cluster if possible
    diff = [r for r in recs if int(r.get("vibe_cluster", -1)) not in (dominant, -1)]
    if diff:
        return random.choice(diff)

    # else sample from full dataset in other clusters
    alt = movies_df[movies_df["vibe_cluster"] != dominant]
    if not alt.empty:
        alt_top = alt.sort_values("avg_rating", ascending=False).head(100)
        row = alt_top.sample(1).iloc[0]
        return _row_to_public(int(row.name))

    # final fallback
    return random.choice(recs) if recs else None


# ---------------------------
# Emotion pipeline (optional) and helper
# ---------------------------
try:
    from transformers import pipeline
    emotion_pipeline = pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        return_all_scores=True
    )
except Exception:
    emotion_pipeline = None

def _extract_top_dict(results):
    """
    Normalize HF pipeline outputs.
    - results can be list[dict] or list[list[dict]]
    Returns the dict with the highest 'score'.
    """
    try:
        if not results:
            return None

        # Case A: nested list form
        if isinstance(results, list) and isinstance(results[0], list):
            candidates = results[0]

        # Case B: flat list of dicts
        elif isinstance(results, list) and isinstance(results[0], dict):
            candidates = results

        else:
            return None

        return max(candidates, key=lambda d: d.get("score", 0.0))

    except Exception:
        return None
