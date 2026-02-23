from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


@dataclass
class UserContext:
    """
    Simple container for context about the viewing situation.

    hour         : current hour (0–23)
    is_weekend   : True if today is Saturday or Sunday
    viewing_mode : "solo" or "group"
    """
    hour: int
    is_weekend: bool
    viewing_mode: str  # "solo" | "group"

    @property
    def day_type(self) -> str:
        """
        Return 'weekday' or 'weekend' based on is_weekend flag.
        """
        return "weekend" if self.is_weekend else "weekday"

    @property
    def time_of_day(self) -> str:
        """
        Return a coarse time-of-day label for this context.

        One of: "morning", "afternoon", "evening", "late_night".
        """
        return classify_time_of_day(self.hour)


def build_context(viewing_mode: str) -> UserContext:
    """
    Build a UserContext object from the current time and the given viewing mode.

    viewing_mode should come from the frontend (e.g., a toggle: 'solo' / 'group').
    """
    # Normalize viewing_mode (fallback to "solo" if something unexpected comes in)
    viewing_mode_norm = (viewing_mode or "solo").strip().lower()
    if viewing_mode_norm not in {"solo", "group"}:
        viewing_mode_norm = "solo"

    now = datetime.now()

    return UserContext(
        hour=now.hour,
        is_weekend=now.weekday() >= 5,  # 5 = Saturday, 6 = Sunday
        viewing_mode=viewing_mode_norm,
    )


def classify_time_of_day(hour: int) -> str:
    """
    Map an hour (0–23) into a simple time-of-day label.

    - 05–11 : morning
    - 12–17 : afternoon
    - 18–21 : evening
    - 22–04 : late_night
    """
    if 5 <= hour <= 11:
        return "morning"
    elif 12 <= hour <= 17:
        return "afternoon"
    elif 18 <= hour <= 21:
        return "evening"
    else:
        return "late_night"


def context_to_preferences(ctx: UserContext) -> Dict[str, Any]:
    """
    Convert a UserContext into high-level preference hints that
    the recommender can use.

    Returns a dictionary like:

    {
        "time_of_day": "evening",
        "mood_boost": ["calm", "fantasy"],
        "genre_boost": ["Comedy", "Family"],
        "notes": "Weekend group evening – fun, light movies."
    }

    This function does NOT call any model. It just encodes rules.
    """
    time_label = classify_time_of_day(ctx.hour)

    # Start with empty preferences
    mood_boost = []
    genre_boost = []
    notes_parts = []

    # Rule 1: Time-of-day rules
    if time_label == "late_night":
        # Late night: calm, softer content
        mood_boost.extend(["calm", "sad"])  # calm / reflective vibes
        genre_boost.extend(["Drama", "Documentary"])
        notes_parts.append("late-night, so we prefer calmer, softer content")
    elif time_label == "evening":
        # Evening: mixed, but slightly fun / relaxing
        mood_boost.extend(["happy", "romantic"])
        genre_boost.extend(["Comedy", "Romance"])
        notes_parts.append("evening, good time for feel-good or romantic movies")
    elif time_label == "afternoon":
        # Afternoon: can handle more action / adventure
        mood_boost.extend(["action", "fantasy"])
        genre_boost.extend(["Action", "Adventure", "Sci-Fi"])
        notes_parts.append("afternoon, okay for more energetic content")
    else:  # morning
        mood_boost.extend(["calm", "happy"])
        genre_boost.extend(["Drama", "Family"])
        notes_parts.append("morning, favouring lighter or thoughtful content")

    # Rule 2: Weekend vs weekday
    if ctx.is_weekend:
        # Weekends: more fun, more action/comedy
        mood_boost.append("happy")
        genre_boost.extend(["Comedy", "Action", "Family"])
        notes_parts.append("weekend, so we boost fun, family and action genres")
    else:
        notes_parts.append("weekday, slightly more balanced mix")

    # Rule 3: Viewing mode
    if ctx.viewing_mode == "group":
        # Group: less experimental, more broadly likeable
        genre_boost.extend(["Comedy", "Family"])
        mood_boost.append("happy")
        notes_parts.append("group mode, so we boost crowd-pleaser genres")
    else:  # solo
        notes_parts.append("solo mode, okay to show more personal / niche picks")

    # Remove duplicates while preserving order
    def dedupe(seq):
        seen = set()
        out = []
        for x in seq:
            if x not in seen:
                out.append(x)
                seen.add(x)
        return out

    mood_boost = dedupe(mood_boost)
    genre_boost = dedupe(genre_boost)

    return {
        "time_of_day": time_label,
        "mood_boost": mood_boost,
        "genre_boost": genre_boost,
        "notes": "; ".join(notes_parts),
    }


def describe_context(ctx: UserContext) -> str:
    """
    Human-readable description of the context.

    Useful for logging, debugging, or showing in an admin/analytics UI.
    """
    return (
        f"time_of_day={ctx.time_of_day}, "
        f"day_type={ctx.day_type}, "
        f"viewing_mode={ctx.viewing_mode}"
    )
