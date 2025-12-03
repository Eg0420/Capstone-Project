import os
import sys
import pandas as pd

# --- FIX 1: Add project root to Python path ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Now app/ becomes importable
from app.db import SessionLocal, init_db
from app.models import Movie

# --- Load cleaned CSV ---
df = pd.read_csv("data/movies_cleaned.csv")

# --- Insert into DB ---
def seed():
    init_db()
    db = SessionLocal()

    for _, row in df.iterrows():
        movie = Movie(
            movie_id=str(row["movie_id"]),
            title=row["title"],
            year=int(row["year"]),
            genres=row.get("genres","")
        )
        db.add(movie)

    db.commit()
    db.close()
    print("🎉 Movies seeded into database!")

if __name__ == "__main__":
    seed()
