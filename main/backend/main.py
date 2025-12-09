from fastapi import FastAPI
from notebooks import vyber_ai_mood_recommender


app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/mood_input")
def mood_input(data: dict):
    return {"mood": "neutral"}  # temporary

@app.get("/recommendations")
def recommendations(mood: str):
    movies = vyber_ai_mood_recommender(mood)
    return {"mood": mood, "results": movies}
