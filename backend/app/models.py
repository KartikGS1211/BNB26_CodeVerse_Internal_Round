from __future__ import annotations

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(64), default="Idea")
    updatedAt: Mapped[str] = mapped_column(String(64), default="just now")
    thumbnail: Mapped[str | None] = mapped_column(String(512), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)


class Script(Base):
    __tablename__ = "scripts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    projectId: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    topic: Mapped[str] = mapped_column(String(255), default="")
    niche: Mapped[str] = mapped_column(String(255), default="")
    tone: Mapped[str] = mapped_column(String(255), default="")
    platform: Mapped[str] = mapped_column(String(255), default="")
    lines: Mapped[list] = mapped_column(JSON, default=list)


class Mapping(Base):
    __tablename__ = "mappings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    projectId: Mapped[str] = mapped_column(String(64), index=True)
    scriptLineId: Mapped[str] = mapped_column(String(64))
    start: Mapped[float] = mapped_column(Float)
    end: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)


class Clip(Base):
    __tablename__ = "clips"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    projectId: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    start: Mapped[float] = mapped_column(Float)
    end: Mapped[float] = mapped_column(Float)
    score: Mapped[int] = mapped_column(Integer)
    hook: Mapped[str] = mapped_column(Text, default="")
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    platformCaptions: Mapped[dict] = mapped_column(JSON, default=dict)


class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(32))
    src: Mapped[str] = mapped_column(String(512), default="")
    thumbnail: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    createdAt: Mapped[str] = mapped_column(String(64), default="")
    has_transcript: Mapped[bool] = mapped_column(Boolean, default=False)


class TranscriptWord(Base):
    __tablename__ = "transcript_words"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assetId: Mapped[str] = mapped_column(String(64), index=True)
    word: Mapped[str] = mapped_column(Text)
    start: Mapped[float] = mapped_column(Float)
    end: Mapped[float] = mapped_column(Float)
    order: Mapped[int] = mapped_column(Integer)


class Timeline(Base):
    __tablename__ = "timelines"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    clipId: Mapped[str] = mapped_column(String(64), default="")
    aspect: Mapped[str] = mapped_column(String(8), default="9:16")
    tracks: Mapped[list] = mapped_column(JSON, default=list)


class WorkflowCard(Base):
    __tablename__ = "workflow_cards"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    column: Mapped[str] = mapped_column(String(32))
    platform: Mapped[str] = mapped_column(String(64))
    dueDate: Mapped[str] = mapped_column(String(64), default="")
    owner: Mapped[str | None] = mapped_column(String(64), nullable=True)


class InsightMetric(Base):
    __tablename__ = "insight_metrics"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    label: Mapped[str] = mapped_column(String(128))
    value: Mapped[float] = mapped_column(Float)
    change: Mapped[float] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(16), nullable=True)


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    clipId: Mapped[str] = mapped_column(String(64))
    clipTitle: Mapped[str] = mapped_column(String(255))
    platform: Mapped[str] = mapped_column(String(64))
    scheduledAt: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="scheduled")


class RenderJob(Base):
    __tablename__ = "render_jobs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timelineId: Mapped[str] = mapped_column(String(64))
    platform: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    outputUrl: Mapped[str | None] = mapped_column(String(512), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    createdAt: Mapped[str] = mapped_column(String(64), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    passwordHash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255), default="")
    createdAt: Mapped[str] = mapped_column(String(64), server_default=func.now())
