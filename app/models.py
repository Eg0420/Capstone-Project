from app.db import Base  # relative import
from sqlalchemy import Column, Integer, String, Float

class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    genre = Column(String, nullable=True)
    release_year = Column(Integer, nullable=True)
    rating = Column(Float, nullable=True)


