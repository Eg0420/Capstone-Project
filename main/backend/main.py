from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/mood_input")
def mood_input(data: dict):
    return {"mood": "neutral"}  # temporary

@app.get("/recommendations")
def recommendations(mood: str):
    return {"mood": mood, "results": []}  # temporary
