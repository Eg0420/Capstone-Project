import pandas as pd

def clean_movies(in_path="data/movies.csv", out_path="data/movies_cleaned.csv"):
    df = pd.read_csv(in_path)

    df.columns = df.columns.str.lower()
    df.rename(columns={"movieid": "movie_id"}, inplace=True)

    df["year"] = df["title"].str.extract(r"\((\d{4})\)", expand=False)
    df["title"] = df["title"].str.replace(r"\(\d{4}\)", "", regex=True).str.strip()

    df["genres"] = df["genres"].fillna("").replace("(no genres listed)", "")

    df.to_csv(out_path, index=False)
    print("Created:", out_path)

if __name__ == "__main__":
    clean_movies()
