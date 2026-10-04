from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ScheduledPost
from app.schemas import ScheduledPostOut, SchedulePostRequest

router = APIRouter()


@router.post("/publish/schedule", response_model=ScheduledPostOut)
def schedule_post(body: SchedulePostRequest, db: Session = Depends(get_db)):
    post = ScheduledPost(
        id=f"p-{uuid.uuid4().hex[:8]}",
        clipId=body.clipId,
        clipTitle=body.clipTitle,
        platform=body.platform,
        scheduledAt=body.scheduledAt,
        status="scheduled",
    )
    db.add(post)
    db.commit()
    return post


@router.get("/publish/schedule", response_model=list[ScheduledPostOut])
def list_scheduled(db: Session = Depends(get_db)):
    return db.query(ScheduledPost).order_by(ScheduledPost.scheduledAt).all()


@router.patch("/publish/schedule/{post_id}", response_model=ScheduledPostOut)
def update_post(post_id: str, status: str = "published", db: Session = Depends(get_db)):
    post = db.get(ScheduledPost, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    post.status = status
    db.commit()
    return post
