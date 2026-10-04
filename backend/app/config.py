from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
RENDER_DIR = DATA_DIR / "renders"
DB_PATH = DATA_DIR / "creatorai.db"

for _d in (DATA_DIR, UPLOAD_DIR, RENDER_DIR):
    _d.mkdir(parents=True, exist_ok=True)


class Settings:
    database_url: str = f"sqlite:///{DB_PATH}"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    whisper_model: str = "base"
    use_llm: bool = False
    simulated_render: bool = True
    demo_mode: bool = True

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", self.database_url)
        origins = os.getenv("CORS_ORIGINS")
        if origins:
            self.cors_origins = [o.strip() for o in origins.split(",") if o.strip()]
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model = os.getenv("GEMINI_MODEL", self.gemini_model)
        self.whisper_model = os.getenv("WHISPER_MODEL", self.whisper_model)
        self.use_llm = os.getenv("USE_LLM", "").lower() in ("1", "true", "yes") and bool(self.gemini_api_key)
        self.simulated_render = os.getenv("SIMULATED_RENDER", "").lower() not in ("0", "false", "no")
        self.demo_mode = os.getenv("DEMO_MODE", "1").lower() not in ("0", "false", "no")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
