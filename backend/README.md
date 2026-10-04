# CreatorAi backend

FastAPI backend for the CreatorAi creator-workflow platform. Implements the
full API contract in [`../docs/API_CONTRACT.md`](../docs/API_CONTRACT.md) and
mirrors the frontend's demo data exactly, so the app behaves the same with
`NEXT_PUBLIC_USE_MOCK=true` (frontend mocks) or `false` (this backend).

## Run

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # or: py -3.13 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

Then in `frontend/.env.local`:

```bash
NEXT_PUBLIC_USE_MOCK=false
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Open http://localhost:3000 — the studio, asset search, script/hook
generation, clip detection, timeline assistant, renders, workflow board,
insights, and publishing all run against this backend.

## What's real vs. simulated

Every feature works with zero API keys (deterministic heuristic engines),
and upgrades when tooling is available:

| Feature | Offline | With tooling |
|---|---|---|
| Script + hook generation | template engine, scored hooks | `OPENAI_API_KEY` + `USE_LLM=true` |
| Script→footage alignment | token-similarity + monotonic DP over the bundled transcript | same algorithm on Whisper transcripts |
| Clip detection | explainable heuristic scoring (hook signal, completeness, emotion, length, alignment confidence) | LLM rescoring via the same pipeline |
| Moment search | TF-IDF cosine over transcript sentences | same, richer transcripts |
| Transcription of uploads | marked pending | `pip install openai-whisper` |
| Rendering | simulated job with progress polling | FFmpeg: real cuts, aspect reframing, burned captions, music mix |

## Architecture

```
app/
  main.py            FastAPI app, CORS, lifespan (create tables + seed)
  config.py          env settings
  db.py              SQLAlchemy engine/session (SQLite by default)
  models.py          ORM models (camelCase fields = API contract)
  schemas.py         Pydantic request/response models
  seed.py            demo data (mirrors frontend src/mocks/demo.ts)
  routers/           projects, scripts, assets, search, timelines,
                     workflow, insights, publish, assistant
  services/
    alignment.py     script→transcript alignment (DP) — core differentiator
    clips.py         candidate segments → scored clips with reasons
    generator.py     script + hook generation
    assistant.py     natural-language timeline edits
    render.py        FFmpeg rendering with simulated fallback
    search.py        natural-language moment search
    transcripts.py   whisper transcription, ffprobe, thumbnails, auto-tags
    llm.py           optional OpenAI wrapper
tests/               pytest suite (TestClient) — 19 tests
```

Data persists to `backend/data/creatorai.db` (SQLite). Uploads land in
`backend/data/uploads/`, renders in `backend/data/renders/`.

## Tests

```bash
.venv\Scripts\python -m pytest tests/ -q
```

## Scaling notes (post-hackathon)

- Swap `DATABASE_URL` to PostgreSQL + pgvector for real embedding search.
- Move `render.py` jobs to Celery/RabbitMQ (or BullMQ) when rendering at scale.
- Add auth (the current API is open for the demo).
