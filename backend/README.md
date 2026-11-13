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

## API endpoints
- `GET /health`
- `GET /api/v1/config`
- `POST /api/v1/songs` — creates original Bengali/Hindi lyrics using Gemini API and stores a project record.
- `GET /api/v1/songs/{id}` — retrieves a project.
- `POST /api/v1/songs/{id}/generate-music` — submits lyrics to the native ACE-Step REST API at `ACESTEP_WORKER_URL/release_task`.
- `GET /api/v1/songs/{id}/music-status` — checks the ACE-Step asynchronous task and stores its result.
- `GET /api/v1/songs/{id}/audio` — securely proxies the generated audio from the private worker.

## ACE-Step GPU worker connection
Set these environment variables on the Render backend:
- `ACESTEP_WORKER_URL`: private HTTPS base URL of the ACE-Step REST API server, normally exposed on port 8001. Do not use the Gradio UI URL.
- `ACESTEP_API_KEY`: same secret configured as `ACESTEP_API_KEY` on the GPU worker.

The backend now speaks ACE-Step's native asynchronous API:
1. `POST /release_task` submits a job.
2. `POST /query_result` checks job progress.
3. `GET /v1/audio?path=...` retrieves the completed MP3.

Music submission explicitly sets `thinking=false`, disables LM formatting/caption helpers, and supplies duration/BPM/key/time-signature metadata. This selects ACE-Step's DiT text-to-music path and avoids requiring the optional 5Hz LM to be initialized. The DiT music model still requires a compatible GPU worker.

See [../worker/README.md](../worker/README.md) for GPU worker setup. Do not expose the worker API key to Android clients.

## Free-first model selection
- Lyrics: Gemini API free tier where available; quota and model availability vary by account and can change.
- Music: ACE-Step self-hosted. No unlimited free cloud GPU is assumed.
- Images: planned ComfyUI + a separately licensed image checkpoint.
- MP4: FFmpeg on the worker.
- YouTube: official YouTube Data API v3 + OAuth user consent.

## Production notes
The current SQLite store is suitable for development only. Use a persistent disk or managed PostgreSQL before public deployment; ephemeral containers can lose local database files. Add authentication, per-user ownership, rate limiting, job queueing, upload limits and signed download URLs before exposing this API publicly.
