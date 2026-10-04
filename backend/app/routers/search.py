from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Asset, TranscriptWord
from app.schemas import TranscriptMoment
from app.services.alignment import group_utterances
from app.services.search import build_index, search_moments

router = APIRouter()


@router.get("/search/moments", response_model=list[TranscriptMoment])
def search_moments_endpoint(q: str = "", db: Session = Depends(get_db)):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter q is required")

    assets = db.query(Asset).filter(Asset.has_transcript.is_(True)).all()
    moments: list[dict] = []
    for asset in assets:
        words = (
            db.query(TranscriptWord)
            .filter(TranscriptWord.assetId == asset.id)
            .order_by(TranscriptWord.start)
            .all()
        )
        if not words:
            continue
        docs = build_index(asset.id, words)
        found = search_moments(docs, q, limit=5)
        moments.extend(found)

    moments.sort(key=lambda m: m["start"])
    return [TranscriptMoment(**m) for m in moments[:10]]


@router.get("/search/utterances")
def list_utterances(asset_id: str = "asset-1", db: Session = Depends(get_db)):
    words = (
        db.query(TranscriptWord)
        .filter(TranscriptWord.assetId == asset_id)
        .order_by(TranscriptWord.start)
        .all()
    )
    groups = group_utterances(words)
    return [
        {
            "text": " ".join(w.word for w in group),
            "start": group[0].start,
            "end": group[-1].end,
        }
        for group in groups
    ]
