import uvicorn
from fastapi import FastAPI

app = FastAPI(
    title="Information Warfare Analyzer",
    description="Analyzes media articles for similarities to known information warfare narratives",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


def start():
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
