# Context-Aware Personalization Rules 

This document explains how the **context-aware personalization module** works in Vyber.
The goal is to change recommendations based on the situation in which the user is watching:
- time of day,
- weekend vs weekday,
- solo vs group watching.

The idea is to keep this logic lightweight and transparent (simple rules), not a heavy black-box model.

---

## 1. What problem this solves

A pure recommendation model only looks at **movies** and sometimes **user history**.  
However, in real life, people watch different types of movies in different situations:

- Late at night they may want calm or soft content.
- On weekends with friends they may want fun, easy, crowd-pleaser movies.
- In the afternoon they may be okay with more energetic action or fantasy.

The context module captures this **situation** and turns it into small “boost signals” for the main recommender.

---

## 2. Context schema

We represent context using a simple dataclass:

- `hour` (int): current hour (0–23)
- `is_weekend` (bool): True if today is Saturday or Sunday
- `viewing_mode` (str): "solo" or "group", selected by the user in the UI

The context is built from the system clock and the viewing mode:

```python
UserContext(
    hour=now.hour,
    is_weekend=now.weekday() >= 5,
    viewing_mode=viewing_mode_norm,
)
