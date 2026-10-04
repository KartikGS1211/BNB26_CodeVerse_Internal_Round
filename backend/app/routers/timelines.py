from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import RenderJob, Timeline
from app.schemas import RenderQueued, RenderStatus, TimelineOut
from app.services import clips as clip_service, render as render_service

router = APIRouter()


@router.get("/timelines/{timeline_id}", response_model=TimelineOut)
def get_timeline(timeline_id: str, db: Session = Depends(get_db)):
    timeline = db.get(Timeline, timeline_id)
    if timeline is not None:
        return timeline

    clip_id = timeline_id.replace("timeline-", "clip-", 1)
    if clip_id != timeline_id:
        from app.models import Clip
        clip = db.get(Clip, clip_id)
        if clip is not None:
            return clip_service.build_timeline(
                {"id": clip.id, "title": clip.title, "start": clip.start,
                 "end": clip.end, "hook": clip.hook},
            )
    raise HTTPException(status_code=404, detail="Timeline not found")


@router.put("/timelines/{timeline_id}", response_model=TimelineOut)
def update_timeline(timeline_id: str, body: TimelineOut, db: Session = Depends(get_db)):
    timeline = db.get(Timeline, timeline_id)
    if timeline is None:
        timeline = Timeline(id=timeline_id)
        db.add(timeline)
    timeline.clipId = body.clipId
    timeline.aspect = body.aspect
    timeline.tracks = [track.model_dump() for track in body.tracks]
    db.commit()
    return timeline


@router.post("/timelines/{timeline_id}/render", response_model=RenderQueued)
def render_timeline(timeline_id: str, platform: str = Query(...), db: Session = Depends(get_db)):
    timeline = db.get(Timeline, timeline_id)
    if timeline is None:
        raise HTTPException(status_code=404, detail="Timeline not found")
    payload = {
        "id": timeline.id,
        "clipId": timeline.clipId,
        "aspect": timeline.aspect,
        "tracks": timeline.tracks,
    }
    job = render_service.queue_render(payload, platform)
    return RenderQueued(renderId=job.id, status=job.status)


@router.get("/renders/{render_id}", response_model=RenderStatus)
def get_render(render_id: str, db: Session = Depends(get_db)):
    job = db.get(RenderJob, render_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Render not found")
    return RenderStatus(
        id=job.id,
        timelineId=job.timelineId,
        platform=job.platform,
        status=job.status,
        progress=job.progress,
        outputUrl=job.outputUrl,
        note=job.note,
        error=job.error,
    )
