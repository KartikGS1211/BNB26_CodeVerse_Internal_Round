"""Gemini integration for real script/hook generation and clip scoring.
Falls back to heuristic engines when no key is configured."""
from __future__ import annotations

import json
import time

from app.config import get_settings


def llm_json(prompt: str, system: str, temperature: float = 0.7, retries: int = 3) -> dict | None:
    settings = get_settings()
    if not settings.use_llm:
        return None
    try:
        from google import genai
    except ImportError:
        return None
    client = genai.Client(api_key=settings.gemini_api_key)
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config={
                    "system_instruction": system,
                    "temperature": temperature,
                    "response_mime_type": "application/json",
                },
            )
            text = response.text or "{}"
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(text)
        except Exception as exc:
            if attempt < retries - 1 and "503" in str(exc):
                time.sleep(2 ** attempt)
                continue
            import logging
            logging.getLogger(__name__).error("Gemini call failed: %s", exc)
            return None
    return None
