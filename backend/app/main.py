from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import DATA_DIR, RENDER_DIR, UPLOAD_DIR, get_settings
from app.db import Base, engine
from app.routers import assets, assistant, auth, insights, publish, projects, scripts
from app.routers import search as search_router
from app.routers import timelines, workflow
from app.seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_if_empty()
    yield


app = FastAPI(title="CreatorAi API", version="1.0.0", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes are mounted at the root because the frontend's api.ts calls
# `${API_URL}/projects`, `${API_URL}/timelines/${id}`, etc.
app.include_router(projects.router, tags=["projects"])
app.include_router(scripts.router, tags=["scripts"])
app.include_router(assets.router, tags=["assets"])
app.include_router(search_router.router, tags=["search"])
app.include_router(timelines.router, tags=["timelines"])
app.include_router(workflow.router, tags=["workflow"])
app.include_router(insights.router, tags=["insights"])
app.include_router(publish.router, tags=["publish"])
app.include_router(assistant.router, tags=["assistant"])
app.include_router(auth.router, tags=["auth"])


@app.get("/health")
def health():
    return {"status": "ok", "demo_mode": settings.demo_mode}


UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/renders", StaticFiles(directory=RENDER_DIR), name="renders")
app.mount("/media", StaticFiles(directory=DATA_DIR / "demo"), name="media")
