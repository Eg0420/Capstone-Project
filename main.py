from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from pydantic import BaseModel

from .db import SessionLocal, init_db
from .models import Movie, User, UserMood, Feedback

load_dotenv()
init_db()  # Create tables when server starts

app = FastAPI(title="Vyber Backend")


# ---------- DB Dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Health Check ----------
@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- Response Models ----------
class MovieOut(BaseModel):
    movie_id: str
    title: str
    year: int | None
    genres: str
    avg_rating: float | None

    class Config:
        orm_mode = True


# ---------- Movies ----------
@app.get("/movies/top", response_model=list[MovieOut])
def get_top_movies(limit: int = 10, db: Session = Depends(get_db)):
    movies = db.query(Movie).order_by(Movie.avg_rating.desc()).limit(limit).all()
    return movies


@app.get("/movies/genre/{genre}", response_model=list[MovieOut])
def get_movies_by_genre(genre: str, limit: int = 10, db: Session = Depends(get_db)):
    movies = db.query(Movie).filter(Movie.genres.ilike(f"%{genre}%")) \
                            .order_by(Movie.avg_rating.desc()).limit(limit).all()
    return movies


# ---------- Mood Logging ----------
class MoodIn(BaseModel):
    user_id: str | None = None
    mood: str
    raw_text: str | None = None
    sentiment_score: float | None = None


@app.post("/mood")
def log_mood(payload: MoodIn, db: Session = Depends(get_db)):
    user = None
    if payload.user_id:
        user = db.query(User).filter_by(user_id=payload.user_id).first()
        if not user:
            user = User(user_id=payload.user_id)
            db.add(user)
            db.commit()

    mood = UserMood(
        user_id=user.id if user else None,
        mood=payload.mood,
        raw_text=payload.raw_text,
        sentiment_score=payload.sentiment_score,
    )
    db.add(mood)
    db.commit()

    return {"status": "success", "mood_id": mood.id}


# ---------- Feedback ----------
class FeedbackIn(BaseModel):
    user_id: str | None = None
    movie_id: str
    mood: str | None = None
    feedback: str


@app.post("/feedback")
def add_feedback(payload: FeedbackIn, db: Session = Depends(get_db)):
    user = None
    if payload.user_id:
        user = db.query(User).filter_by(user_id=payload.user_id).first()
        if not user:
            user = User(user_id=payload.user_id)
            db.add(user)
            db.commit()

    movie = db.query(Movie).filter_by(movie_id=payload.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    fb = Feedback(
        user_id=user.id if user else None,
        movie_id=movie.id,
        mood=payload.mood,
        feedback=payload.feedback,
    )
    db.add(fb)
    db.commit()

    return {"status": "ok", "feedback_id": fb.id}
