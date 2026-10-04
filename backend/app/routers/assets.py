from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR
from app.db import get_db
from app.models import Asset, TranscriptWord
from app.schemas import AssetOut
from app.services import transcripts as transcript_service

router = APIRouter()


@router.get("/assets", response_model=list[AssetOut])
def list_assets(q: str = "", db: Session = Depends(get_db)):
    query = db.query(Asset)
    if q:
        query = query.filter(Asset.name.ilike(f"%{q}%"))
    return query.all()


@router.post("/assets/upload", response_model=AssetOut)
async def upload_asset(request: Request, db: Session = Depends(get_db)):
    """Accepts a real multipart file, or the frontend's JSON shape
    ({name, type}) when called without a file."""
    file: UploadFile | None = None
    name: str | None = None
    media_type: str | None = None

    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        name = form.get("name")
        media_type = form.get("type")
    else:
        try:
            body = await request.json()
            name = body.get("name")
            media_type = body.get("type")
        except Exception:
            pass

    asset_id = f"asset-{uuid.uuid4().hex[:8]}"
    saved_path: Path | None = None

    if file is not None and getattr(file, "filename", None):
        filename = file.filename
        detected = (file.content_type or "video").split("/")[0]
        media_type = detected if detected in ("video", "audio", "image") else "video"
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "mp4"
        saved_path = UPLOAD_DIR / f"{asset_id}.{ext}"
        with open(saved_path, "wb") as handle:
            handle.write(await file.read())
        src = f"/uploads/{saved_path.name}"
    else:
        filename = name or "uploaded-asset"
        media_type = media_type or "video"
        src = ""

    duration = transcript_service.probe_duration(saved_path) if saved_path else None
    thumbnail = transcript_service.make_thumbnail(saved_path, asset_id) if saved_path else None

    asset = Asset(
        id=asset_id,
        name=filename,
        type=media_type,
        src=src,
        duration=duration,
        thumbnail=thumbnail,
        tags=transcript_service.auto_tags(filename, media_type),
        createdAt=date.today().isoformat(),
        has_transcript=False,
    )
    db.add(asset)
    db.commit()

    if saved_path:
        words = transcript_service.transcribe(saved_path)
        if words:
            for order, word in enumerate(words):
                db.add(TranscriptWord(assetId=asset_id, order=order, **word))
            asset.has_transcript = True
            db.commit()

    return asset


@router.get("/assets/{asset_id}/transcript")
def get_transcript(asset_id: str, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    words = (
        db.query(TranscriptWord)
        .filter(TranscriptWord.assetId == asset_id)
        .order_by(TranscriptWord.start)
        .all()
    )
    return {"assetId": asset_id, "hasTranscript": asset.has_transcript, "words": words}


@router.get("/uploads/{filename}")
def uploaded_file(filename: str):
    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)
