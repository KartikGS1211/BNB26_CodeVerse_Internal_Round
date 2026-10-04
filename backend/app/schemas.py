from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AssetOut(BaseModel):
    id: str
    name: str
    type: str
    src: str = ""
    thumbnail: str | None = None
    duration: float | None = None
    tags: list[str] = Field(default_factory=list)
    createdAt: str = ""


class ProjectOut(BaseModel):
    id: str
    title: str
    status: str
    updatedAt: str
    thumbnail: str | None = None
    progress: int = 0


class ScriptLine(BaseModel):
    id: str
    text: str
    order: int


class ScriptOut(BaseModel):
    id: str
    projectId: str
    title: str
    lines: list[ScriptLine] = Field(default_factory=list)
    topic: str = ""
    niche: str = ""
    tone: str = ""
    platform: str = ""


class MappingOut(BaseModel):
    scriptLineId: str
    start: float
    end: float
    confidence: float


class ClipOut(BaseModel):
    id: str
    title: str
    start: float
    end: float
    score: int
    reasons: list[str] = Field(default_factory=list)
    hook: str = ""
    platformCaptions: dict[str, str] = Field(default_factory=dict)


class TrackItem(BaseModel):
    id: str
    start: float
    end: float
    text: str | None = None
    src: str | None = None
    style: dict[str, Any] = Field(default_factory=dict)


class Track(BaseModel):
    type: str
    items: list[TrackItem] = Field(default_factory=list)


class TimelineOut(BaseModel):
    id: str
    clipId: str = ""
    aspect: str = "9:16"
    tracks: list[Track] = Field(default_factory=list)


class ProjectDetail(BaseModel):
    project: ProjectOut
    script: ScriptOut | None = None
    mappings: list[MappingOut] = Field(default_factory=list)
    clips: list[ClipOut] = Field(default_factory=list)


class ScriptGenerateRequest(BaseModel):
    topic: str
    niche: str = ""
    tone: str = ""
    platform: str = ""


class HookGenerateRequest(BaseModel):
    scriptId: str = ""


class HookVariant(BaseModel):
    id: str
    text: str
    score: int


class AssetUploadRequest(BaseModel):
    name: str
    type: str = "video"


class TranscriptMoment(BaseModel):
    text: str
    start: float
    end: float
    assetId: str


class WorkflowCardOut(BaseModel):
    id: str
    title: str
    column: str
    platform: str
    dueDate: str = ""
    owner: str | None = None


class InsightMetricOut(BaseModel):
    id: str
    label: str
    value: float
    change: float
    unit: str | None = None


class InsightsOut(BaseModel):
    metrics: list[InsightMetricOut] = Field(default_factory=list)
    series: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class ScheduledPostOut(BaseModel):
    id: str
    clipId: str
    clipTitle: str
    platform: str
    scheduledAt: str
    status: str


class SchedulePostRequest(BaseModel):
    clipId: str
    clipTitle: str
    platform: str
    scheduledAt: str


class AssistantRequest(BaseModel):
    command: str
    timelineId: str = ""


class AssistantResponse(BaseModel):
    command: str
    timelineId: str
    timeline: TimelineOut | None = None
    applied: list[str] = Field(default_factory=list)


class RenderQueued(BaseModel):
    renderId: str
    status: str


class RenderStatus(BaseModel):
    id: str
    timelineId: str
    platform: str
    status: str
    progress: int
    outputUrl: str | None = None
    note: str | None = None
    error: str | None = None
