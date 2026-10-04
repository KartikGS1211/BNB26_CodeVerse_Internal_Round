from __future__ import annotations

import copy

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Timeline
from app.schemas import AssistantRequest, AssistantResponse
from app.services.assistant import apply_command

router = APIRouter()


@router.post("/assistant/command", response_model=AssistantResponse)
def assistant_command(body: AssistantRequest, db: Session = Depends(get_db)):
    timeline = db.get(Timeline, body.timelineId)
    if timeline is None:
        raise HTTPException(status_code=404, detail="Timeline not found")

    # Deep copy: the service mutates tracks in place, so the payload
    # must not share references with the ORM object (otherwise
    # SQLAlchemy sees old == new and skips the UPDATE).
    payload = {
        "id": timeline.id,
        "clipId": timeline.clipId,
        "aspect": timeline.aspect,
        "tracks": copy.deepcopy(timeline.tracks),
    }
    updated, applied = apply_command(payload, body.command)

    timeline.aspect = updated["aspect"]
    timeline.tracks = updated["tracks"]
    db.commit()

    return AssistantResponse(
        command=body.command,
        timelineId=body.timelineId,
        timeline=updated,
        applied=applied,
    )
