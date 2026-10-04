"""Auto clip generation: build candidate segments from aligned script lines,
score them with explainable features, and trim to sentence boundaries."""
from __future__ import annotations

import re

from app.seed import platform_captions
from app.services.alignment import similarity

EMOTION_WORDS = {
    "burnout", "growth", "system", "honest", "energy", "best", "breakthrough",
    "changed", "love", "hate", "secret", "truth", "mistake", "power", "free",
    "never", "always", "everything", "nothing", "real", "problem", "fix",
}
HOOK_SIGNALS = ("?", "you", "your", "stop", "why", "how", "don't", "do not", "never")


def _has_hook_signal(text: str) -> bool:
    low = text.lower()
    return any(signal in low for signal in HOOK_SIGNALS) or low.endswith("?")


def _is_complete(text: str) -> bool:
    return bool(re.search(r"[.!?]$", text.strip()))


def score_segment(lines: list[str], start: float, end: float, avg_confidence: float) -> tuple[int, list[str]]:
    duration = end - start
    reasons: list[str] = []
    score = 40.0

    if _has_hook_signal(lines[0]):
        score += 20
        reasons.append("Hook within first 3 seconds")
    if _is_complete(lines[-1]):
        score += 12
        reasons.append("Complete thought")
    emotion_hits = sum(1 for line in lines for word in EMOTION_WORDS if word in line.lower())
    if emotion_hits >= 2:
        score += 14
        reasons.append("Strong emotional peak")
    elif emotion_hits == 1:
        score += 7
        reasons.append("Emotional language detected")
    if 12 <= duration <= 60:
        score += 10
        reasons.append("Ideal short-form length")
    elif duration > 90:
        score -= 8
    elif duration < 8:
        score -= 6
    if avg_confidence > 0.85:
        score += 8
        reasons.append("High transcript alignment confidence")
    if len(lines) >= 2:
        score += 4
        reasons.append("High audience relevance")
    if not reasons:
        reasons.append("Clean visual section")

    return int(max(5, min(99, round(score)))), reasons[:4]


def generate_clips(script_lines: list[str], mappings: list[dict], max_clips: int = 6) -> list[dict]:
    """Candidate windows of 2-4 consecutive aligned lines, scored and de-overlapped."""
    if not script_lines or not mappings:
        return []

    by_line = {m["scriptLineId"]: m for m in mappings}
    ordered_texts = [line for line in script_lines]

    candidates = []
    for size in (2, 3, 4):
        for start_idx in range(len(ordered_texts) - size + 1):
            chunk = ordered_texts[start_idx:start_idx + size]
            maps = [by_line.get(f"line-{start_idx + k + 1}") for k in range(size)]
            if any(m is None for m in maps):
                continue
            start = maps[0]["start"]
            end = maps[-1]["end"]
            avg_conf = sum(m["confidence"] for m in maps) / len(maps)
            score, reasons = score_segment(chunk, start, end, avg_conf)
            candidates.append({
                "start_idx": start_idx,
                "end_idx": start_idx + size - 1,
                "start": start,
                "end": end,
                "score": score,
                "reasons": reasons,
                "lines": chunk,
            })

    candidates.sort(key=lambda c: c["score"], reverse=True)
    chosen: list[dict] = []
    used: set[int] = set()
    for cand in candidates:
        idxs = set(range(cand["start_idx"], cand["end_idx"] + 1))
        if idxs & used:
            continue
        used |= idxs
        chosen.append(cand)
        if len(chosen) >= max_clips:
            break
    chosen.sort(key=lambda c: c["start"])

    clips = []
    for i, cand in enumerate(chosen):
        title = " ".join(cand["lines"][0].split()[:7]).rstrip(".,!?")
        if len(title) > 60:
            title = title[:57] + "..."
        clips.append({
            "id": f"clip-{i + 1}",
            "title": title.title() if title.islower() else title,
            "start": cand["start"],
            "end": cand["end"],
            "score": cand["score"],
            "hook": cand["lines"][0],
            "reasons": cand["reasons"],
            "platformCaptions": platform_captions(title),
        })
    return clips


def build_timeline(clip: dict, asset_src: str = "/demo/sample.mp4", aspect: str = "9:16") -> dict:
    """Create an editable JSON timeline for a clip: video cut + caption items + music bed."""
    duration = clip["end"] - clip["start"]
    return {
        "id": f"timeline-{clip['id']}",
        "clipId": clip["id"],
        "aspect": aspect,
        "tracks": [
            {"type": "video", "items": [{"id": "v1", "start": 0, "end": duration, "src": asset_src}]},
            {"type": "caption", "items": [
                {"id": "c1", "start": 0, "end": min(duration, 6), "text": clip["hook"]},
                {"id": "c2", "start": min(duration, 6), "end": duration,
                 "text": clip["title"]},
            ]},
            {"type": "music", "items": [{"id": "m1", "start": 0, "end": duration,
                                          "src": "lofi-focus.mp3", "style": {"volume": 0.18}}]},
        ],
    }


def hook_variants_for_clip(clip: dict) -> list[dict]:
    hook_text = clip.get("hook", "")
    base = hook_text
    variants = [base]
    if similarity(base, base) >= 0:
        variants = [
            base,
            base.replace(".", "!") if base.endswith(".") else base + "!",
            f"Here's what nobody tells you: {base[0].lower() + base[1:]}",
        ]
    return [{"id": f"hv{i + 1}", "text": t, "score": 90 - i * 6} for i, t in enumerate(variants[:3])]
