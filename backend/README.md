# SurajSong backend

## Run locally
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY="your-key"
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `/health` and `/docs`.

## Secrets
Copy `.env.example` into your deployment provider's environment settings. Do not commit real keys and do not embed provider keys in the Android app.

## Current endpoints
- `GET /health`
- `GET /api/v1/config`
- `POST /api/v1/songs` — creates original Bengali/Hindi lyrics using Gemini API and stores a project record.
- `GET /api/v1/songs/{id}` — retrieves a project.
- `POST /api/v1/songs/{id}/generate-music` — forwards lyrics to a configured ACE-Step worker at `ACESTEP_WORKER_URL/generate`.

## Music worker contract
The private worker must expose `POST /generate` and accept JSON:
```json
{
  "project_id": "uuid",
  "lyrics": "[Verse 1]...",
  "language": "bn",
  "duration_minutes": 4,
  "style_prompt": "melodic Bengali pop",
  "seed": 123
}
```
It should return a JSON job identifier/status and a private output reference. Do not expose worker credentials to Android clients.

## Free-first model selection
- Lyrics: Gemini API free tier where available; quota and model availability vary by account and can change.
- Music: ACE-Step self-hosted. The project repository is Apache-2.0 and documents generation up to four minutes; actual throughput depends on GPU. Verify the exact downloaded checkpoint's license before commercial use.
- Images: planned ComfyUI + a separately licensed image checkpoint.
- MP4: FFmpeg on the worker.
- YouTube: official YouTube Data API v3 + OAuth user consent.

There is no promise of unlimited free cloud GPU. Self-hosted generation is free of per-call API fees only if you already have suitable hardware; electricity, storage and hosting still have costs. A free cloud host is not a dependable GPU music-generation service.

## Production notes
The current SQLite store is suitable for development only. Use a persistent disk or managed PostgreSQL before public deployment; ephemeral containers can lose local database files. Add authentication, per-user ownership, rate limiting, job queueing, upload limits and signed download URLs before exposing this API publicly.
