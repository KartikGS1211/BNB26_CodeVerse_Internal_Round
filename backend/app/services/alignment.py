"""Script-to-footage alignment: maps each script line to a timestamp span in the
transcript using token similarity + a monotonic dynamic-programming assignment.

This is the core differentiator: semantic match with order constraints,
robust to reworded transcripts (Whisper output) and extra footage.
"""
from __future__ import annotations

import difflib
import re

from app.db import SessionLocal
from app.models import TranscriptWord

PUNCT_RE = re.compile(r"[^\w\s]")


def normalize(text: str) -> str:
    return PUNCT_RE.sub(" ", text.lower()).strip()


def tokens(text: str) -> list[str]:
    return normalize(text).split()


def similarity(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return difflib.SequenceMatcher(None, ta, tb).ratio()


def group_utterances(words: list[TranscriptWord], gap_seconds: float = 0.5) -> list[list[TranscriptWord]]:
    if not words:
        return []
    ordered = sorted(words, key=lambda w: (w.start, w.order))
    groups: list[list[TranscriptWord]] = [[ordered[0]]]
    for prev, word in zip(ordered, ordered[1:]):
        ends_sentence = bool(re.search(r"[.!?]$", prev.word))
        gap = word.start - prev.end
        if ends_sentence or gap >= gap_seconds:
            groups.append([word])
        else:
            groups[-1].append(word)
    return groups


def align_script_to_transcript(script_lines: list[str], words: list[TranscriptWord]) -> list[dict]:
    """Return [{'scriptLineId', 'start', 'end', 'confidence'}] in script order."""
    utterances = group_utterances(words)
    if not utterances or not script_lines:
        return []

    u_text = [" ".join(w.word for w in group) for group in utterances]
    n, m = len(script_lines), len(utterances)

    sim = [[similarity(line, u_text[j]) for j in range(m)] for line in script_lines]

    NEG = float("-inf")
    dp = [[NEG] * m for _ in range(n)]
    back = [[-1] * m for _ in range(n)]
    for j in range(m):
        dp[0][j] = sim[0][j]
    for i in range(1, n):
        best_k, best_val = -1, NEG
        for j in range(m):
            if best_k >= 0:
                dp[i][j] = best_val + sim[i][j]
                back[i][j] = best_k
            if dp[i - 1][j] > best_val:
                best_val = dp[i - 1][j]
                best_k = j

    last = max(range(m), key=lambda j: dp[n - 1][j])
    if dp[n - 1][last] == NEG:
        return []

    path = [0] * n
    j = last
    for i in range(n - 1, -1, -1):
        path[i] = j
        j = back[i][j] if i > 0 else 0

    results = []
    for i, line in enumerate(script_lines):
        group = utterances[path[i]]
        start = group[0].start
        end = group[-1].end
        confidence = sim[i][path[i]]
        confidence = max(0.35, min(0.99, confidence + 0.08))
        results.append({
            "scriptLineId": f"line-{i + 1}",
            "start": round(start, 2),
            "end": round(end, 2),
            "confidence": round(confidence, 3),
        })
    return results


def get_asset_words(asset_id: str) -> list[TranscriptWord]:
    db = SessionLocal()
    try:
        return (
            db.query(TranscriptWord)
            .filter(TranscriptWord.assetId == asset_id)
            .order_by(TranscriptWord.start)
            .all()
        )
    finally:
        db.close()
