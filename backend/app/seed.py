"""Seed data mirroring the frontend demo exactly, so the app behaves identically
with NEXT_PUBLIC_USE_MOCK=false (real backend) or true (frontend mocks)."""
from __future__ import annotations

import re

from app.db import SessionLocal
from app.models import (
    Asset, Clip, InsightMetric, Mapping, Project, ScheduledPost, Script,
    Timeline, TranscriptWord, WorkflowCard,
)

LINE_TEXTS = [
    "Most creators do not have an idea problem — they have a system problem.",
    "I spent years chasing every new format and burning out by Friday.",
    "Growth changed when I started treating one strong idea like a creative asset.",
    "First, capture the raw thought before you polish it.",
    "Then turn that thought into a clear promise for one specific audience.",
    "Record the long version while your energy is still honest.",
    "The best short clips are already hiding inside that conversation.",
    "Look for complete thoughts, emotional turns, and a fast opening hook.",
    "Do not let automation flatten your voice.",
    "Use AI to find the moments, then keep the edits in your hands.",
    "One recording can become a short, a carousel, a post, and a newsletter.",
    "Change the packaging for each platform, not the core message.",
    "Consistency gets easier when every step hands off to the next one.",
    "Your workflow should save your creative energy for the decisions that matter.",
    "Build the system once, and let every idea travel further.",
]

PROJECTS = [
    {"id": "grow-creator", "title": "How to grow as a creator", "status": "Editing", "updatedAt": "12 min ago", "progress": 74},
    {"id": "pricing-story", "title": "The pricing lesson nobody tells you", "status": "Clips ready", "updatedAt": "Yesterday", "progress": 88},
    {"id": "studio-tour", "title": "My minimal studio setup", "status": "Script", "updatedAt": "2 days ago", "progress": 32},
]

SCRIPT = {
    "id": "script-grow", "projectId": "grow-creator", "title": "How to grow as a creator",
    "topic": "Sustainable creator growth", "niche": "Creator education",
    "tone": "Warm & direct", "platform": "YouTube",
}

CONFIDENCE = [0.97, .9, .84, .94, .76, .92, .88, .95, .68, .91, .86, .79, .93, .72, .96]

HOOKS = [
    {"id": "h1", "text": "You don't need more ideas. You need a system.", "score": 96},
    {"id": "h2", "text": "The creator burnout loop nobody talks about.", "score": 89},
    {"id": "h3", "text": "One video can power your entire content week.", "score": 93},
    {"id": "h4", "text": "Stop creating from scratch every single day.", "score": 86},
    {"id": "h5", "text": "This is how smart creators make every idea travel further.", "score": 82},
]

CLIP_ROWS = [
    ("clip-1", "You have a system problem", 0, 24, 98, "You don't need more ideas. You need a system."),
    ("clip-2", "Find the clips already hiding", 43, 68, 94, "Your best short-form content is already recorded."),
    ("clip-3", "Keep the edit in your hands", 65, 83, 91, "AI should accelerate your taste, not replace it."),
    ("clip-4", "One recording, five formats", 78, 101, 87, "One recording can power your entire week."),
    ("clip-5", "The consistency handoff", 96, 113, 76, "Consistency is a workflow problem."),
    ("clip-6", "Make every idea travel", 105, 120, 60, "Build the system once."),
]

PLATFORM_CAPTION_TEMPLATES = {
    "YouTube Shorts": "{title} — save this workflow for your next recording. #CreatorTips #ContentStrategy",
    "Instagram Reels": "{title} ✦ Build once, publish everywhere. #creatoreconomy #contentcreator",
    "TikTok": "{title}. Here's the creator system I wish I had sooner. #CreatorTok #growth",
    "LinkedIn": "{title}. A practical lesson in building a sustainable content engine.",
    "X": "{title}. One idea → many useful formats.",
}

ASSET_NAMES = ["Creator growth master", "Studio b-roll", "Desk close-up", "Podcast audio", "Pricing story", "Walking intro"]
ASSET_TYPES = ["video", "image", "video", "audio"]
ASSET_TAGS = [["creator", "talking head"], ["b-roll", "studio"], ["workspace", "detail"], ["voice", "clean audio"]]

TIMELINE = {
    "id": "timeline-grow", "clipId": "clip-1", "aspect": "9:16",
    "tracks": [
        {"type": "video", "items": [
            {"id": "v1", "start": 0, "end": 10, "src": "/media/sample.mp4"},
            {"id": "v2", "start": 10.5, "end": 24, "src": "/media/sample.mp4"},
        ]},
        {"type": "caption", "items": [
            {"id": "c1", "start": 0, "end": 6, "text": "You don't need more ideas"},
            {"id": "c2", "start": 6, "end": 12, "text": "You need a system"},
            {"id": "c3", "start": 12, "end": 24, "text": "Turn one strong idea into an asset"},
        ]},
        {"type": "music", "items": [
            {"id": "m1", "start": 0, "end": 24, "src": "lofi-focus.mp3", "style": {"volume": 0.18}},
        ]},
    ],
}

WORKFLOW_CARDS = [
    ("w1", "Creator myths worth unlearning", "Idea", "TikTok", "Oct 5"),
    ("w2", "Pricing without panic", "Script", "YouTube", "Oct 6"),
    ("w3", "Studio tour — autumn", "Recorded", "Reels", "Oct 7"),
    ("w4", "How to grow as a creator", "Editing", "Shorts", "Today"),
    ("w5", "Three hook formulas", "Scheduled", "TikTok", "Oct 4"),
    ("w6", "Build a creative system", "Published", "LinkedIn", "Oct 2"),
]

INSIGHT_METRICS = [
    {"id": "views", "label": "Total views", "value": 284700, "change": 18.4},
    {"id": "watch", "label": "Avg. watch time", "value": 24.8, "change": 7.2, "unit": "s"},
    {"id": "retention", "label": "Completion rate", "value": 68, "change": 11.3, "unit": "%"},
    {"id": "followers", "label": "New followers", "value": 4280, "change": 22.8},
]

VIEWS_SERIES = [18, 24, 21, 31, 37, 33, 48, 52, 46, 61, 68, 72]

SCHEDULED_POSTS = [
    {"id": "p1", "clipId": "clip-5", "clipTitle": "The consistency handoff",
     "platform": "Instagram Reels", "scheduledAt": "2026-10-04T18:30:00", "status": "scheduled"},
]


def transcript_words() -> list[dict]:
    words: list[dict] = []
    for i, line in enumerate(LINE_TEXTS):
        cleaned = re.sub(r"[—,.]", "", line)
        parts = cleaned.split()
        base = i * 7.5
        per = 6 / len(parts)
        for j, word in enumerate(parts):
            words.append({
                "assetId": "asset-1", "word": word,
                "start": round(base + j * per, 3),
                "end": round(base + (j + 0.86) * per, 3),
                "order": len(words),
            })
    return words


def platform_captions(title: str) -> dict[str, str]:
    return {platform: template.format(title=title) for platform, template in PLATFORM_CAPTION_TEMPLATES.items()}


def clip_reasons(index: int) -> list[str]:
    if index % 2:
        return ["Complete thought", "Strong emotional peak", "Clean visual section"]
    return ["Hook within first 3 seconds", "Complete thought", "High audience relevance"]


def seed_if_empty() -> None:
    db = SessionLocal()
    try:
        if db.query(Project).count():
            return
        for p in PROJECTS:
            db.add(Project(**p))
        db.add(Script(**SCRIPT, lines=[{"id": f"line-{i + 1}", "text": t, "order": i} for i, t in enumerate(LINE_TEXTS)]))
        for i, conf in enumerate(CONFIDENCE):
            db.add(Mapping(projectId="grow-creator", scriptLineId=f"line-{i + 1}",
                           start=i * 7.5, end=i * 7.5 + 6.2, confidence=conf))
        for i, row in enumerate(CLIP_ROWS):
            cid, title, start, end, score, hook = row
            db.add(Clip(id=cid, projectId="grow-creator", title=title, start=start, end=end,
                        score=score, hook=hook, reasons=clip_reasons(i),
                        platformCaptions=platform_captions(title)))
        for i in range(12):
            db.add(Asset(
                id=f"asset-{i + 1}",
                name=ASSET_NAMES[i % 6] + (f" {i + 1}" if i > 5 else ""),
                type=ASSET_TYPES[i % 4],
                src="/demo/sample.mp4",
                duration=None if i % 4 == 1 else 40 + i * 7,
                tags=ASSET_TAGS[i % 4],
                createdAt=f"2026-09-{str(28 - i).zfill(2)}",
                has_transcript=(i == 0),
            ))
        for w in transcript_words():
            db.add(TranscriptWord(**w))
        db.add(Timeline(**TIMELINE))
        for cid, title, column, platform, due in WORKFLOW_CARDS:
            db.add(WorkflowCard(id=cid, title=title, column=column, platform=platform, dueDate=due))
        for m in INSIGHT_METRICS:
            db.add(InsightMetric(**m))
        for p in SCHEDULED_POSTS:
            db.add(ScheduledPost(**p))
        db.commit()
    finally:
        db.close()
