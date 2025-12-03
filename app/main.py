from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel #new package import
from app import models          # absolute import
from app.db import engine, get_db  # absolute import

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vyber Movies API") #gave title


# Pydantic model for creating a movie
class MovieCreate(BaseModel):
    movie_id: str
    title: str
    genre: str | None = None
    release_year: int | None = None
    rating: float | None = None

# Root endpoint for friendly message
@app.get("/")
def root():
    return {"message": "Welcome to Vyber Movies API! Visit /docs for API documentation."}    

@app.get("/movies")
def read_movies(db: Session = Depends(get_db)):
    return db.query(models.Movie).all()


# ✅ POST multiple movies at once
@app.post("/movies/batch")
def create_movies(movies: list[MovieCreate], db: Session = Depends(get_db)):
    db_movies = []
    for movie in movies:
        db_movie = models.Movie(
            movie_id=movie.movie_id,
            title=movie.title,
            genre=movie.genre,
            release_year=movie.release_year,
            rating=movie.rating
        )
        db.add(db_movie)
        db_movies.append(db_movie)
    db.commit()
    # Refresh all new movies to get their IDs
    for db_movie in db_movies:
        db.refresh(db_movie)
    return db_movies
