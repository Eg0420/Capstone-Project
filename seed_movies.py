import csv
from app.db import SessionLocal, init_db
from app.models import Movie

init_db()

def seed(path="data/movies_cleaned.csv"):
    db = SessionLocal()

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if db.query(Movie).filter_by(movie_id=r["movie_id"]).first():
                continue

            movie = Movie(
                movie_id=r["movie_id"],
                title=r["title"],
                year=int(r["year"]) if r["year"] else None,
                genres=r.get("genres", ""),
                avg_rating=float(r["avg_rating"]) if r["avg_rating"] else None,
            )
            db.add(movie)

        db.commit()

    db.close()
    print("Movies loaded successfully!")


if __name__ == "__main__":
    seed()
