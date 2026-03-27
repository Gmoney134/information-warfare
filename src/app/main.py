from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.database import init_db
from app.domains import load_domains
from app.routers import narrative_scores


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    load_domains()
    yield


app = FastAPI(
    title="Information Warfare Analyzer",
    description="Analyzes media articles for similarities to known information warfare narratives",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(narrative_scores.router)


def start():
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
