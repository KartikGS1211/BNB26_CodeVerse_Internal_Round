from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Asset, Clip, Mapping, Project, Script, Timeline
from app.schemas import (
    ClipOut, MappingOut, ProjectDetail, ProjectOut, ScriptOut, TimelineOut,
)
from app.services import clips as clip_service
from app.services.alignment import align_script_to_transcript, get_asset_words

router = APIRouter()


def _source_words(db: Session) -> list:
    asset = db.query(Asset).filter(Asset.has_transcript.is_(True)).first()
    if asset is None:
        asset = db.query(Asset).filter(Asset.type == "video").first()
    if asset is None:
        return []
    return get_asset_words(asset.id)


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()


@router.get("/projects/{project_id}", response_model=ProjectDetail)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    script = db.query(Script).filter(Script.projectId == project_id).first()
    mappings = db.query(Mapping).filter(Mapping.projectId == project_id).all()
    clips = db.query(Clip).filter(Clip.projectId == project_id).all()
    return {
        "project": project,
        "script": script,
        "mappings": mappings,
        "clips": clips,
    }


@router.post("/projects/{project_id}/map", response_model=list[MappingOut])
def map_project(project_id: str, db: Session = Depends(get_db)):
    script = db.query(Script).filter(Script.projectId == project_id).first()
    if script is None:
        raise HTTPException(status_code=404, detail="No script for this project")
    words = _source_words(db)
    if not words:
        raise HTTPException(status_code=404, detail="No transcript available")
    lines = [line["text"] for line in (script.lines or []) if isinstance(line, dict)]
    results = align_script_to_transcript(lines, words)

    db.query(Mapping).filter(Mapping.projectId == project_id).delete()
    for result in results:
        db.add(Mapping(projectId=project_id, **result))
    db.commit()
    return db.query(Mapping).filter(Mapping.projectId == project_id).all()


@router.post("/projects/{project_id}/clips/generate", response_model=list[ClipOut])
def generate_clips(project_id: str, db: Session = Depends(get_db)):
    script = db.query(Script).filter(Script.projectId == project_id).first()
    if script is None:
        raise HTTPException(status_code=404, detail="No script for this project")
    words = _source_words(db)
    if not words:
        raise HTTPException(status_code=404, detail="No transcript available")
    lines = [line["text"] for line in (script.lines or []) if isinstance(line, dict)]
    mappings = align_script_to_transcript(lines, words)

    db.query(Mapping).filter(Mapping.projectId == project_id).delete()
    for result in mappings:
        db.add(Mapping(projectId=project_id, **result))

    new_clips = clip_service.generate_clips(lines, mappings)
    db.query(Clip).filter(Clip.projectId == project_id).delete()
    for clip in new_clips:
        db.add(Clip(projectId=project_id, **clip))
    db.commit()
    return db.query(Clip).filter(Clip.projectId == project_id).all()


@router.get("/projects/{project_id}/timeline", response_model=TimelineOut)
def project_timeline(project_id: str, db: Session = Depends(get_db)):
    clip = db.query(Clip).filter(Clip.projectId == project_id).first()
    timeline = db.query(Timeline).filter(Timeline.clipId == (clip.id if clip else "")).first()
    if timeline is None and clip is not None:
        return clip_service.build_timeline(
            {"id": clip.id, "title": clip.title, "start": clip.start,
             "end": clip.end, "hook": clip.hook},
        )
    if timeline is None:
        raise HTTPException(status_code=404, detail="No timeline for this project")
    return timeline
