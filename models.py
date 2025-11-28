from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    year = Column(Integer, nullable=True)
    genres = Column(String)
    runtime = Column(Integer, nullable=True)
    avg_rating = Column(Float, nullable=True)
    metadata = Column(Text, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class UserMood(Base):
    __tablename__ = "user_moods"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    mood = Column(String)
    sentiment_score = Column(Float, nullable=True)
    raw_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    movie_id = Column(Integer, ForeignKey("movies.id"))
    mood = Column(String)
    feedback = Column(String)  # like/dislike or 👍/👎
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
