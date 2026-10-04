"""Natural-language timeline editing: the chat assistant.

Parses commands like 'shorten to 30s', 'remove silences',
'make clip 3 punchier', 'add caption ... at 12s' and mutates
the timeline JSON server-side. Every edit stays inspectable in JSON.
"""
from __future__ import annotations

import re

NUMBER_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*(s|sec|secs|second|seconds|min|mins|minutes)?")


def _total_duration(timeline: dict) -> float:
    ends = [item["end"] for track in timeline.get("tracks", []) for item in track.get("items", [])]
    return max(ends) if ends else 0.0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def shorten_to(timeline: dict, seconds: float) -> list[str]:
    applied = []
    for track in timeline.get("tracks", []):
        before = len(track.get("items", []))
        track["items"] = [
            item for item in track.get("items", []) if item["start"] < seconds
        ]
        if len(track["items"]) < before:
            applied.append(f"Dropped {before - len(track['items'])} item(s) past {seconds:.0f}s in {track['type']} track")
        for item in track.get("items", []):
            if item["end"] > seconds:
                item["end"] = max(item["start"] + 0.5, seconds)
                applied.append(f"Trimmed {item['id']} to end at {item['end']:.1f}s")
    return applied or [f"Timeline already fits within {seconds:.0f}s"]


def remove_silences(timeline: dict, gap_threshold: float = 1.0) -> list[str]:
    applied = []
    for track in timeline.get("tracks", []):
        items = sorted(track.get("items", []), key=lambda x: x["start"])
        for prev, item in zip(items, items[1:]):
            gap = item["start"] - prev["end"]
            if gap >= gap_threshold:
                shift = gap
                for other in items:
                    if other["start"] >= item["start"]:
                        other["start"] = round(other["start"] - shift, 3)
                        other["end"] = round(other["end"] - shift, 3)
                applied.append(f"Closed a {gap:.1f}s silence gap in {track['type']} track")
                break
    return applied or ["No silences above 1s detected"]


def punch_up(timeline: dict) -> list[str]:
    applied = []
    for track in timeline.get("tracks", []):
        if track["type"] == "caption":
            for item in track.get("items", []):
                item.setdefault("style", {})
                item["style"]["preset"] = "karaoke"
                item["style"]["highlight"] = True
            applied.append("Upgraded captions to karaoke style")
        if track["type"] == "music":
            for item in track.get("items", []):
                style = item.setdefault("style", {})
                style["volume"] = min(0.35, float(style.get("volume", 0.18)) + 0.08)
            applied.append("Raised music bed volume")
        if track["type"] == "video":
            for item in track.get("items", []):
                style = item.setdefault("style", {})
                style["zoom"] = 1.08
                style["focus"] = "center"
            applied.append("Added subtle punch-in zoom")
    return applied or ["Nothing to punch up on an empty timeline"]


def add_caption(timeline: dict, text: str, at: float) -> list[str]:
    captions = next((t for t in timeline.get("tracks", []) if t["type"] == "caption"), None)
    if captions is None:
        captions = {"type": "caption", "items": []}
        timeline.setdefault("tracks", []).append(captions)
    start = _clamp(at, 0, _total_duration(timeline))
    item = {
        "id": f"c-{len(captions['items']) + 1}-{abs(hash(text)) % 10000}",
        "start": round(start, 2),
        "end": round(min(start + 3.0, _total_duration(timeline)), 2),
        "text": text,
    }
    captions["items"].append(item)
    return [f"Added caption '{text}' at {start:.1f}s"]


def delete_item(timeline: dict, item_id: str) -> list[str]:
    for track in timeline.get("tracks", []):
        before = len(track.get("items", []))
        track["items"] = [i for i in track.get("items", []) if i["id"] != item_id]
        if len(track["items"]) < before:
            return [f"Deleted {item_id} from {track['type']} track"]
    return [f"No item named '{item_id}' found"]


def reframe(timeline: dict, aspect: str) -> list[str]:
    timeline["aspect"] = aspect
    return [f"Reframed timeline to {aspect}"]


def apply_command(timeline: dict, command: str) -> tuple[dict, list[str]]:
    """Parse a natural-language editing command against the timeline."""
    c = command.lower().strip()
    applied: list[str] = []

    if re.search(r"\b(remove|cut|delete)\b.*\bsilence", c) or c == "remove silences":
        applied += remove_silences(timeline)

    if re.search(r"\b(shorten|trim|cut)\b.*\b(to|down to)\b", c) or re.search(r"\bmake it\b.*\b(second|sec)", c):
        match = NUMBER_RE.search(c)
        if match:
            value = float(match.group(1))
            unit = match.group(2) or "s"
            seconds = value * 60 if unit.startswith("min") else value
            applied += shorten_to(timeline, seconds)

    if "punch" in c or "punchier" in c or "energy" in c:
        applied += punch_up(timeline)

    if "silence" in c and not applied:
        applied += remove_silences(timeline)

    caption_match = re.search(r"(?:add|insert)\s+(?:a\s+)?caption\s+[\"']?(.+?)[\"']?\s+at\s+(\d+(?:\.\d+)?)", c)
    if caption_match:
        applied += add_caption(timeline, caption_match.group(1), float(caption_match.group(2)))

    delete_match = re.search(r"\b(delete|remove|drop)\s+(?:item|clip|track)?\s*([a-z]+-\w+)", c)
    if delete_match:
        applied += delete_item(timeline, delete_match.group(2))

    aspect_match = re.search(r"\b(9:16|1:1|16:9)\b", c)
    if aspect_match:
        applied += reframe(timeline, aspect_match.group(1))

    if not applied:
        applied = ["No timeline edit matched that command — try 'shorten to 30s', 'remove silences', or 'make it punchier'"]

    return timeline, applied
