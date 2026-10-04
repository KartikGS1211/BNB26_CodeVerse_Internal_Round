from __future__ import annotations

import time

from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.main import app


@contextmanager
def client():
    with TestClient(app) as c:
        yield c


def test_health():
    with client() as c:
        r = c.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_list_projects():
    with client() as c:
        r = c.get("/projects")
        assert r.status_code == 200
        projects = r.json()
        assert len(projects) == 3
        assert projects[0]["id"] == "grow-creator"
        assert projects[0]["progress"] == 74


def test_project_detail():
    with client() as c:
        r = c.get("/projects/grow-creator")
        assert r.status_code == 200
        data = r.json()
        assert data["project"]["title"] == "How to grow as a creator"
        assert len(data["script"]["lines"]) == 15
        assert len(data["mappings"]) == 15
        assert len(data["clips"]) == 6
        assert data["clips"][0]["score"] == 98
        assert data["clips"][0]["reasons"]
        assert "YouTube Shorts" in data["clips"][0]["platformCaptions"]


def test_generate_script():
    with client() as c:
        r = c.post("/scripts/generate", json={
            "topic": "Pricing your creative work",
            "niche": "Creator education",
            "tone": "Bold",
            "platform": "TikTok",
        })
        assert r.status_code == 200
        script = r.json()
        assert script["topic"] == "Pricing your creative work"
        assert 8 <= len(script["lines"]) <= 15
        assert all(line["text"] for line in script["lines"])


def test_generate_hooks():
    with client() as c:
        r = c.post("/hooks/generate", json={"scriptId": "script-grow"})
        assert r.status_code == 200
        hooks = r.json()
        assert len(hooks) == 5
        assert all(0 < h["score"] <= 99 for h in hooks)
        assert all(h["text"] for h in hooks)


def test_map_project():
    with client() as c:
        r = c.post("/projects/grow-creator/map")
        assert r.status_code == 200
        mappings = r.json()
        assert len(mappings) == 15
        for m in mappings:
            assert 0.35 <= m["confidence"] <= 0.99
            assert m["end"] > m["start"]
        starts = [m["start"] for m in mappings]
        assert starts == sorted(starts)
        # identical transcript text should align near-perfectly
        assert mappings[0]["confidence"] > 0.9


def test_generate_clips():
    with client() as c:
        r = c.post("/projects/grow-creator/clips/generate")
        assert r.status_code == 200
        clips = r.json()
        assert 1 <= len(clips) <= 6
        for clip in clips:
            assert 0 <= clip["score"] <= 99
            assert clip["reasons"]
            assert clip["platformCaptions"]["TikTok"]
            assert clip["end"] > clip["start"]


def test_assets_list_and_filter():
    with client() as c:
        assert len(c.get("/assets").json()) == 12
        q = c.get("/assets", params={"q": "creator"}).json()
        assert q and all("creator" in a["name"].lower() or any(
            "creator" in t for t in a["tags"]) for a in q)
        assert c.get("/assets", params={"q": "zzz-nothing"}).json() == []


def test_upload_asset_json():
    with client() as c:
        r = c.post("/assets/upload", json={"name": "pricing-talk.mp4", "type": "video"})
        assert r.status_code == 200
        asset = r.json()
        assert asset["name"] == "pricing-talk.mp4"
        assert asset["type"] == "video"
        assert asset["tags"]


def test_search_moments():
    with client() as c:
        r = c.get("/search/moments", params={"q": "pricing"})
        assert r.status_code == 200
        r2 = c.get("/search/moments", params={"q": "growth changed"})
        moments = r2.json()
        assert moments
        assert all("text" in m and "start" in m and "assetId" in m for m in moments)


def test_timeline_roundtrip():
    with client() as c:
        r = c.get("/timelines/timeline-grow")
        assert r.status_code == 200
        timeline = r.json()
        assert timeline["id"] == "timeline-grow"
        assert {t["type"] for t in timeline["tracks"]} == {"video", "caption", "music"}

        timeline["aspect"] = "1:1"
        r = c.put("/timelines/timeline-grow", json=timeline)
        assert r.status_code == 200
        assert r.json()["aspect"] == "1:1"

        r = c.put("/timelines/timeline-grow", json={**timeline, "aspect": "9:16"})
        assert r.status_code == 200


def test_render_lifecycle():
    with client() as c:
        r = c.post("/timelines/timeline-grow/render", params={"platform": "TikTok"})
        assert r.status_code == 200
        render_id = r.json()["renderId"]
        assert r.json()["status"] == "queued"

        deadline = time.time() + 30
        status = None
        while time.time() < deadline:
            status = c.get(f"/renders/{render_id}").json()
            if status["status"] in ("done", "failed"):
                break
            time.sleep(0.5)
        assert status["status"] == "done"
        assert status["progress"] == 100


def test_workflow():
    with client() as c:
        cards = c.get("/workflow").json()
        assert len(cards) == 6
        r = c.patch("/workflow/w1", json={**cards[0], "column": "Script"})
        assert r.status_code == 200
        assert r.json()["column"] == "Script"
        c.patch("/workflow/w1", json={**cards[0], "column": "Idea"})


def test_insights():
    with client() as c:
        r = c.get("/insights")
        assert r.status_code == 200
        data = r.json()
        assert len(data["metrics"]) == 4
        assert data["metrics"][0]["id"] == "views"
        assert data["series"]
        assert data["recommendations"]


def test_publish_schedule():
    with client() as c:
        r = c.post("/publish/schedule", json={
            "clipId": "clip-1",
            "clipTitle": "You have a system problem",
            "platform": "TikTok",
            "scheduledAt": "2026-10-06T19:45:00",
        })
        assert r.status_code == 200
        post = r.json()
        assert post["status"] == "scheduled"
        assert post["id"]
        posts = c.get("/publish/schedule").json()
        assert any(p["id"] == post["id"] for p in posts)


def test_assistant_shorten():
    with client() as c:
        base = c.get("/timelines/timeline-grow").json()
        test_tl = {**base, "id": "timeline-test"}
        c.put("/timelines/timeline-test", json=test_tl)

        r = c.post("/assistant/command", json={
            "command": "shorten to 12s", "timelineId": "timeline-test",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["applied"]
        timeline = body["timeline"]
        for track in timeline["tracks"]:
            for item in track["items"]:
                assert item["end"] <= 12.0


def test_assistant_remove_silences():
    with client() as c:
        base = c.get("/timelines/timeline-grow").json()
        test_tl = {**base, "id": "timeline-test2"}
        c.put("/timelines/timeline-test2", json=test_tl)

        r = c.post("/assistant/command", json={
            "command": "remove silences", "timelineId": "timeline-test2",
        })
        assert r.status_code == 200
        assert r.json()["applied"]


def test_assistant_unknown_command():
    with client() as c:
        r = c.post("/assistant/command", json={
            "command": "do something weird", "timelineId": "timeline-grow",
        })
        assert r.status_code == 200
        assert "No timeline edit matched" in r.json()["applied"][0]


def test_alignment_with_reworded_transcript():
    from app.models import TranscriptWord
    from app.services.alignment import align_script_to_transcript

    script = ["The quick brown fox jumps over the lazy dog.",
              "Creators need systems not hacks.",
              "Ship every single week."]
    words = []
    t = 0.0
    reworded = [
        "the quick brown fox jumps over a lazy dog",
        "creators need systems not hacks",
        "so ship every single week",
    ]
    for sentence in reworded:
        for word in sentence.split():
            words.append(TranscriptWord(word=word, start=t, end=t + 0.4, order=len(words)))
            t += 0.45
        t += 0.8

    results = align_script_to_transcript(script, words)
    assert len(results) == 3
    assert results[0]["confidence"] > 0.7
    assert results[1]["confidence"] > 0.9
    starts = [r["start"] for r in results]
    assert starts == sorted(starts)
