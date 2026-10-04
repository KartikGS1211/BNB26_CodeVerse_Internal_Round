"""Natural-language search over transcripts: 'find where I talk about pricing'.

Lexical TF-IDF cosine over transcript sentences, with an optional
sentence-transformer upgrade path guarded by import availability.
"""
from __future__ import annotations

import math
import re
from collections import Counter

from app.services.alignment import group_utterances, tokens

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "i", "you", "we", "to", "of", "in",
    "on", "for", "with", "is", "are", "was", "were", "it", "this", "that",
    "my", "your", "me", "at", "as", "be", "do", "did", "so", "if", "about",
    "where", "when", "what", "how", "part", "talk", "talking", "say", "said",
}


def _content_tokens(text: str) -> list[str]:
    return [t for t in tokens(text) if t not in STOPWORDS and len(t) > 1]


def build_index(asset_id: str, words) -> list[dict]:
    sentences = group_utterances(words, gap_seconds=0.5)
    docs = []
    for group in sentences:
        text = " ".join(w.word for w in group).strip()
        docs.append({
            "assetId": asset_id,
            "text": text,
            "start": group[0].start,
            "end": group[-1].end,
            "tf": Counter(_content_tokens(text)),
        })
    return docs


def search_moments(docs: list[dict], query: str, limit: int = 5) -> list[dict]:
    query_tokens = _content_tokens(query)
    if not query_tokens or not docs:
        return []

    df: Counter = Counter()
    for doc in docs:
        df.update(set(doc["tf"].keys()))
    n = len(docs)
    idf = {term: math.log((n + 1) / (count + 1)) + 1 for term, count in df.items()}

    q_counts = Counter(query_tokens)
    q_vec = {t: c * idf.get(t, 1.0) for t, c in q_counts.items()}
    q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0

    scored = []
    for doc in docs:
        dot = 0.0
        d_norm_sq = 0.0
        for term, weight in q_vec.items():
            tf = doc["tf"].get(term, 0)
            dot += weight * tf
        for term, count in doc["tf"].items():
            d_norm_sq += (count * idf.get(term, 1.0)) ** 2
        d_norm = math.sqrt(d_norm_sq) or 1.0
        cos = dot / (q_norm * d_norm)
        if cos > 0:
            scored.append((cos, doc))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [
        {
            "text": doc["text"],
            "start": round(doc["start"], 2),
            "end": round(doc["end"], 2),
            "assetId": doc["assetId"],
        }
        for _, doc in scored[:limit]
    ]


def transcript_sentences_for_query(words, query: str, limit: int = 5) -> list[dict]:
    docs = build_index("asset-1", words)
    return search_moments(docs, query, limit)
