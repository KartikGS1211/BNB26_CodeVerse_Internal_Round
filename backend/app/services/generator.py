"""Script and hook generation. Uses the LLM when configured, otherwise a
deterministic template engine that produces structured, platform-aware scripts."""
from __future__ import annotations

import hashlib

from app.services.llm import llm_json

SYSTEM = "You are a creator-strategy copywriter. Return only JSON."

SCRIPT_PROMPT = """Generate a short-form/long-form script about the topic below.
Return JSON: {{"title": str, "lines": [str, ...]}} with 12-15 lines.
Each line is one spoken sentence. Line 1 must be a hook.
Topic: {topic}
Niche: {niche}
Tone: {tone}
Platform: {platform}"""

HOOK_PROMPT = """Given this script, write 5 hook variations (first 3 seconds of a video).
Return JSON: {{"hooks": [{{"text": str, "score": int}}]}} with predicted virality scores 0-100.
Script: {script}"""


def _seed(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest(), 16)


def _pick(items: list, seed: int, offset: int = 0) -> str:
    return items[(seed + offset) % len(items)]


OPENERS = [
    "Most creators do not have an idea problem — they have a system problem.",
    "Nobody talks about the real reason growth stalls.",
    "This one shift changed how I create every single week.",
    "You are not behind. You are just working without a system.",
    "I tried every hack. Only this one stuck.",
]
PROBLEMS = [
    "I spent years chasing every new format and burning out by Friday.",
    "The feed rewards consistency, not chaos.",
    "Most ideas die before they ever reach an audience.",
    "Burnout is a workflow problem wearing a motivation mask.",
]
TURNS = [
    "Growth changed when I started treating one strong idea like a creative asset.",
    "Everything changed when I stopped starting from scratch.",
    "The breakthrough was packaging, not production.",
    "My output doubled when I started reusing my own best work.",
]
STEPS = [
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
]
CLOSERS = [
    "Build the system once, and let every idea travel further.",
    "Start with one idea. Systemize it. Then watch it travel.",
    "Your next upload is already inside your last recording.",
]

HOOK_FORMULAS = [
    "You don't need more ideas. You need a system.",
    "The creator burnout loop nobody talks about.",
    "One video can power your entire content week.",
    "Stop creating from scratch every single day.",
    "This is how smart creators make every idea travel further.",
    "Why your best clip is already recorded and sitting on your hard drive.",
    "The 3-step system behind every creator who seems to post daily.",
    "I stopped creating new content and started packaging old ones. Here's why.",
]

EMOTION_WORDS = ["burnout", "growth", "system", "honest", "energy", "best", "breakthrough", "changed"]


def generate_script(topic: str, niche: str, tone: str, platform: str) -> dict:
    data = llm_json(SCRIPT_PROMPT.format(topic=topic, niche=niche, tone=tone, platform=platform), SYSTEM)
    if data and isinstance(data.get("lines"), list) and data["lines"]:
        return {"title": str(data.get("title") or topic), "lines": [str(x) for x in data["lines"]][:15]}

    seed = _seed(f"{topic}|{niche}|{tone}|{platform}")
    lines = [
        _pick(OPENERS, seed),
        _pick(PROBLEMS, seed, 1),
        _pick(TURNS, seed, 2),
    ]
    pool = STEPS[:]
    count = 9 + seed % 3
    for i in range(count):
        lines.append(pool[(seed + i * 3) % len(pool)])
        if len(set(lines)) < len(lines):
            lines[-1] = pool[(seed + i * 5 + 1) % len(pool)]
    lines = list(dict.fromkeys(lines))
    lines.append(_pick(CLOSERS, seed, 4))
    title = topic if len(topic) < 60 else f"{topic[:57]}..."
    return {"title": title, "lines": lines[:15]}


def score_hook(text: str) -> int:
    words = text.split()
    score = 70
    if text.endswith("?"):
        score += 8
    if any(w.lower() in ("you", "your") for w in words[:4]):
        score += 8
    if len(words) <= 12:
        score += 6
    if any(w in text.lower() for w in EMOTION_WORDS):
        score += 4
    if text.endswith("."):
        score += 2
    return min(99, score)


def generate_hooks(script_text: str, count: int = 5) -> list[dict]:
    data = llm_json(HOOK_PROMPT.format(script=script_text[:2000]), SYSTEM, temperature=0.9)
    if data and isinstance(data.get("hooks"), list) and data["hooks"]:
        hooks = [{"id": f"h{i + 1}", "text": str(h.get("text", "")), "score": int(h.get("score") or 80)}
                 for i, h in enumerate(data["hooks"][:count])]
        if hooks:
            return hooks

    seed = _seed(script_text[:200])
    seen: set[str] = set()
    hooks: list[dict] = []
    for i in range(count):
        text = _pick(HOOK_FORMULAS, seed, i)
        if text in seen:
            text = _pick(HOOK_FORMULAS, seed, i + 7)
        seen.add(text)
        hooks.append({"id": f"h{i + 1}", "text": text, "score": score_hook(text)})
    return hooks
