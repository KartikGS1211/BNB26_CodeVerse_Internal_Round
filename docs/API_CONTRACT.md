# CreatorAi — API Contract

Backend: FastAPI (Python), served from `backend/` (default `http://localhost:8000`).
All payloads use camelCase JSON, matching `frontend/src/types/index.ts`.

The frontend calls these via `src/lib/api.ts`. Set
`NEXT_PUBLIC_USE_MOCK=false` and `NEXT_PUBLIC_API_URL=http://localhost:8000`
to use this backend for real.

## Projects

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/projects` | — | `Project[]` |
| GET | `/projects/{id}` | — | `{ project, script, mappings, clips }` |
| POST | `/projects/{projectId}/map` | — | `Mapping[]` — aligns the project script to the footage transcript (token-similarity + monotonic DP) and persists results |
| POST | `/projects/{projectId}/clips/generate` | — | `Clip[]` — scores candidate segments with explainable reasons, trims to sentence boundaries, persists results |
| GET | `/projects/{projectId}/timeline` | — | `Timeline` |

## Scripts & hooks

| Method | Path | Request | Response |
|---|---|---|---|
| POST | `/scripts/generate` | `{ topic, niche, tone, platform }` | `Script` (12–15 lines, hook first) |
| POST | `/hooks/generate` | `{ scriptId }` | `HookVariant[]` (5 scored variations) |

## Assets

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/assets?q=` | — | `Asset[]` (name/tag filter) |
| POST | `/assets/upload` | JSON `{ name, type }` **or** multipart `file` | `Asset` — multipart uploads are stored, probed for duration, thumbnailed, auto-tagged, and transcribed (Whisper, if installed) |
| GET | `/assets/{id}/transcript` | — | `{ assetId, hasTranscript, words: TranscriptWord[] }` |

## Search

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/search/moments?q=` | — | `TranscriptMoment[]` — natural-language moment search over all transcribed assets (TF-IDF cosine over sentences) |

## Timelines & rendering

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/timelines/{id}` | — | `Timeline` |
| PUT | `/timelines/{id}` | `Timeline` | `Timeline` (upsert) |
| POST | `/timelines/{id}/render?platform=` | — | `{ renderId, status }` — background job |
| GET | `/renders/{renderId}` | — | `{ id, timelineId, platform, status, progress, outputUrl, note, error }` |

Render jobs cut the source footage per the timeline JSON, reframe to the
timeline aspect (9:16 / 1:1 / 16:9), burn captions from the caption track,
and mix the music track — with FFmpeg. Without FFmpeg the job simulates
progress and completes so the UI flow always works.

## Timeline assistant

| Method | Path | Request | Response |
|---|---|---|---|
| POST | `/assistant/command` | `{ command, timelineId }` | `{ command, timelineId, timeline, applied }` — applies the edit server-side and returns the updated timeline JSON |

Supported commands: `shorten to 30s`, `remove silences`, `make it punchier`,
`add caption "text" at 12s`, `delete v2`, `reframe to 9:16`.

## Workflow board

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/workflow` | — | `WorkflowCard[]` |
| PATCH | `/workflow/{id}` | `WorkflowCard` | `WorkflowCard` |
| POST | `/workflow` | `WorkflowCard` | `WorkflowCard` |

## Insights

| Method | Path | Response |
|---|---|---|
| GET | `/insights` | `{ metrics: InsightMetric[], series, recommendations }` |

## Publishing

| Method | Path | Request | Response |
|---|---|---|---|
| POST | `/publish/schedule` | `{ clipId, clipTitle, platform, scheduledAt }` | `ScheduledPost` |
| GET | `/publish/schedule` | — | `ScheduledPost[]` |
| PATCH | `/publish/schedule/{id}?status=published` | — | `ScheduledPost` |

## Health

`GET /health` → `{ status, demo_mode }`

## Timeline JSON schema

```jsonc
{
  "id": "timeline-grow",
  "clipId": "clip-1",
  "aspect": "9:16",            // "9:16" | "1:1" | "16:9"
  "tracks": [
    { "type": "video", "items": [
      { "id": "v1", "start": 0, "end": 10, "src": "/demo/sample.mp4", "style": {} } ] },
    { "type": "caption", "items": [
      { "id": "c1", "start": 0, "end": 6, "text": "You don't need more ideas",
        "style": { "preset": "bold", "highlight": false } } ] },
    { "type": "music", "items": [
      { "id": "m1", "start": 0, "end": 24, "src": "lofi-focus.mp3",
        "style": { "volume": 0.18 } } ] }
  ]
}
```

Every AI edit is stored as this JSON, so the timeline stays draggable,
trimmable, and re-renderable — "AI-generated edits remain editable."

## Configuration

All AI features work offline with deterministic heuristic engines.
Set `OPENAI_API_KEY` + `USE_LLM=true` for LLM-generated scripts/hooks,
install `openai-whisper` for real transcription, and install FFmpeg for
real renders. See `backend/.env.example`.
