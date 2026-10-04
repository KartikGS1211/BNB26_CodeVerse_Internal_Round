"""Transcription + auto-tagging for uploaded assets.

Uses Whisper when installed; otherwise marks the asset as awaiting
transcription so the rest of the pipeline still works.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from app.config import UPLOAD_DIR, get_settings


def probe_duration(path: Path) -> float | None:
    if not shutil.which("ffprobe"):
        return None
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=60,
        )
        return round(float(result.stdout.strip()), 2)
    except Exception:
        return None


def make_thumbnail(path: Path, asset_id: str) -> str | None:
    if not shutil.which("ffmpeg"):
        return None
    thumb = UPLOAD_DIR / f"{asset_id}-thumb.jpg"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-ss", "00:00:01", "-i", str(path),
             "-frames:v", "1", "-q:v", "2", str(thumb)],
            capture_output=True, timeout=120,
        )
        if thumb.exists():
            return f"/uploads/{thumb.name}"
    except Exception:
        pass
    return None


def auto_tags(filename: str, media_type: str) -> list[str]:
    stem = Path(filename).stem
    raw = re.split(r"[-_\s]+", stem)
    tags = [t.lower() for t in raw if len(t) > 1][:4]
    type_tag = {"video": "footage", "audio": "audio", "image": "image"}.get(media_type, "asset")
    return tags + [type_tag]


def transcribe(path: Path) -> list[dict] | None:
    """Return word-level transcript [{word, start, end}] or None if unavailable."""
    try:
        import whisper
    except ImportError:
        return None
    try:
        model = whisper.load_model(get_settings().whisper_model)
        result = model.transcribe(str(path), word_timestamps=True)
        words = []
        for segment in result.get("segments", []):
            for word in segment.get("words", []):
                words.append({
                    "word": word.get("word", "").strip(),
                    "start": round(float(word.get("start", 0)), 3),
                    "end": round(float(word.get("end", 0)), 3),
                })
        return words or None
    except Exception:
        return None
